#!/usr/bin/env python3
"""AXIA D10 offline recorded signal replay. No model training, ROS, network or safety control.

Inputs: original C01 Synthetic test_mixed.csv + separately produced C03 if_scores_test.csv.
Output: ONE standalone HTML file with the immutable input records embedded.
Public code contains no instructor solution or reference score artifact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

RAW_COLS = ('trace_id','sample_idx','timestamp_ns','current_a','torque_nm','accel_mps2','truth_label')
SCORE_COLS = ('trace_id','window_id','timestamp_ns','status','quality_reason','truth_label','risk_score','threshold','prediction')
TRACE_LABELS = ('NORMAL','CURRENT_SPIKE','TORQUE_DRIFT','ACCEL_VIBRATION','INSUFFICIENT_DATA')


def load_csv(path: Path, required: tuple[str,...]) -> list[dict[str,str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(required):
            raise ValueError(f'{path.name} columns mismatch: expected {required}')
        rows=list(reader)
    if not rows or any(None in r for r in rows):
        raise ValueError(f'{path.name} missing/truncated or invalid CSV')
    return rows


def _number(x: str, *, context: str) -> float:
    try: v = float(x)
    except (ValueError,TypeError): raise ValueError(f'{context}: nonnumeric') from None
    if not math.isfinite(v): raise ValueError(f'{context}: nonfinite')
    return v


def validate_and_build(raw_path: Path, scores_path: Path, manifest_path: Path, score_source: str) -> dict:
    """Reject cross-trace joins, false warnings, quality scoring and unrecognized datasets."""
    if not score_source or len(score_source)>90 or any(c in score_source for c in '\n\r\x00'):
        raise ValueError('score_source must be a short provenance label')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('source')!='SYNTHETIC_COURSE_FIXTURE' or manifest.get('seed')!=2409:
        raise ValueError('manifest must be AXIA immutable synthetic seed 2409')
    raw=load_csv(raw_path,RAW_COLS)
    scores=load_csv(scores_path,SCORE_COLS)
    if len(raw)!=1399 or len(scores)!=104:
        raise ValueError('unexpected dataset row count: raw=1399, scores=104 required')
    if manifest.get('expected_rows',{}).get('test_mixed.csv')!=1399:
        raise ValueError('manifest expected_rows mismatch')
    anomaly_cases=manifest.get('anomaly_cases',{})
    quality_cases=manifest.get('quality_cases',{})
    if len(anomaly_cases)!=6 or len(quality_cases)!=4:
        raise ValueError('manifest anomaly/quality cases mismatch')
    raw_map:dict[str,list[dict]]={}
    for r in raw:
        raw_map.setdefault(r['trace_id'],[]).append(r)
    if len(raw_map)!=14 or set(raw_map)!=(set(anomaly_cases)|set(quality_cases)|{f'TST_N_{i:02d}' for i in range(4)}):
        raise ValueError('unexpected trace inventory')
    score_map:dict[tuple[str,int],dict]={}
    for row in scores:
        tid=row['trace_id']
        try:win=int(row['window_id'])
        except ValueError:raise ValueError(f'window invalid for {tid}') from None
        key=(tid,win)
        if key in score_map:raise ValueError(f'duplicate score key {key}')
        score_map[key]=row
    if len(score_map)!=104:raise ValueError('duplicate or missing score windows')
    data=[];t_all=Counter();thresholds=set();warning_positions=[]
    for tid,rows in raw_map.items():
        quality=quality_cases.get(tid)
        expected=99 if quality=='SAMPLE_GAP' else 100
        if len(rows)!=expected:raise ValueError(f'{tid} raw count invalid')
        observed_idx=[];samples=[]
        for r in rows:
            try:idx=int(r['sample_idx']);ts=int(r['timestamp_ns']);label=int(r['truth_label'])
            except ValueError:raise ValueError(f'{tid} raw sample/timestamp/label invalid') from None
            if idx<0 or idx>99 or ts<0 or label not in (-1,0,1):
                raise ValueError(f'{tid} sample_idx/timestamp/truth invalid')
            vals=[None if r[col]=='' else _number(r[col],context=f'{tid}.{col}') for col in RAW_COLS[3:6]]
            observed_idx.append(idx)
            samples.append([idx,ts,*vals,label])
        expected_idxs=[i for i in range(100) if quality!='SAMPLE_GAP' or i!=55]
        if observed_idx!=expected_idxs:raise ValueError(f'{tid} raw sample_idx discontinuity')
        if not quality:
            if any(s[1]!=s[0]*100_000_000 for s in samples):
                raise ValueError(f'{tid} unexpected trace-local timestamp')
            if any((s[-1]==1)!=(40<=s[0]<70 and tid in anomaly_cases) for s in samples):
                raise ValueError(f'{tid} anomaly window truth mismatch')
        else:
            if any(s[-1]!=-1 for s in samples):raise ValueError(f'{tid} quality raw must be -1')
        windows=[]
        for wi in range(1 if quality else 10):
            key=(tid,wi)
            if key not in score_map:raise ValueError(f'{tid} missing window {wi}')
            sr=score_map.pop(key)
            if quality:
                if (sr['status']!='INSUFFICIENT_DATA' or sr['prediction']!='INSUFFICIENT_DATA'
                    or sr['risk_score'] or sr['threshold'] or sr['quality_reason']!=quality
                    or sr['truth_label']!='-1'):
                    raise ValueError(f'{tid} quality trace must not receive model score or NORMAL')
                if sr['timestamp_ns']!=rows[-1]['timestamp_ns']:
                    raise ValueError(f'{tid} quality timestamp mismatch')
                window={'w':0,'timestamp_ns':int(sr['timestamp_ns']),'status':'INSUFFICIENT_DATA',
                        'reason':quality,'truth':-1,'score':None,'threshold':None,'prediction':'INSUFFICIENT_DATA'}
            else:
                block=samples[wi*10:(wi+1)*10]
                if len(block)!=10:raise ValueError(f'{tid} incomplete window')
                if sr['status']!='VALID' or sr['quality_reason']:
                    raise ValueError(f'{tid} valid score status mismatch')
                if int(sr['timestamp_ns'])!=block[-1][1]:
                    raise ValueError(f'{tid} window {wi} timestamp mismatch')
                truth=block[0][-1]
                if any(r[-1]!=truth for r in block) or int(sr['truth_label'])!=truth:
                    raise ValueError(f'{tid} window {wi} truth mismatch')
                score=_number(sr['risk_score'],context=f'{tid}.risk_score')
                limit=_number(sr['threshold'],context=f'{tid}.threshold')
                if sr['prediction']!=('WARNING' if score>limit else 'NORMAL'):
                    raise ValueError(f'{tid} window {wi} prediction/threshold mismatch')
                thresholds.add(limit)
                prediction=sr['prediction']
                case='TP' if truth==1 and prediction=='WARNING' else (
                    'FP' if truth==0 and prediction=='WARNING' else ('FN' if truth==1 else 'TN'))
                t_all[case]+=1
                if prediction=='WARNING':warning_positions.append([tid,wi,case])
                window={'w':wi,'timestamp_ns':int(sr['timestamp_ns']),'status':'VALID',
                    'reason':'','truth':truth,'score':score,'threshold':limit,'prediction':prediction,'case':case}
            windows.append(window)
        data.append({'id':tid,'kind':anomaly_cases.get(tid,'INSUFFICIENT_DATA' if quality else 'NORMAL'),
                     'quality_reason':quality,'samples':samples,'windows':windows})
    if score_map:raise ValueError(f'unmatched score key: {next(iter(score_map))}')
    if len(thresholds)!=1 or sum(t_all.values())!=100:
        raise ValueError('score threshold must be constant across all 100 valid windows')
    if sorted((t['id'] for t in data))!=sorted(set(raw_map)):
        raise ValueError('raw/score trace mismatch')
    conf={key:t_all.get(key,0) for key in ('TP','FP','FN','TN')}
    return {'schema_version':1,'name':'AXIA D10 Isolation Forest Recorded Replay',
        'source':manifest['source'],'score_source':score_source,'seed':2409,
        'ros_actual':False,'gazebo_actual':False,'safety_control_authority':False,
        'raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        'scores_sha256':hashlib.sha256(scores_path.read_bytes()).hexdigest(),
        'confusion':conf,'threshold':next(iter(thresholds)),
        'warnings':warning_positions,'traces':data}


def assert_reference_baseline(payload:dict):
    """Private owner-only release acceptance, not required by public UI smoke tests."""
    expected={'TP':1,'FP':2,'FN':17,'TN':80}
    if payload['confusion']!=expected or abs(payload['threshold']-0.10199750)>1e-8:
        raise ValueError('instructor baseline confusion/threshold mismatch')
    if payload['warnings']!=[['TST_A_00',5,'TP'],['TST_A_03',9,'FP'],['TST_A_04',8,'FP']]:
        raise ValueError('instructor baseline first warning / FP case mismatch')
    if payload['raw_sha256']!='4078e35cb789cf2f468819ad1af8218e95c7489d90a8c24031ec06bc9fff8410':
        raise ValueError('instructor immutable original raw SHA256 mismatch')
    if payload['scores_sha256']!='380eebbab3c83c7ba0fe60f28b25bf9c9f9dc71cd407eafd83114bb55a01ad42':
        raise ValueError('instructor immutable IF reference score SHA256 mismatch')


def render_html(payload:dict,output_path:Path):
    output_path.parent.mkdir(parents=True,exist_ok=True)
    safe_json=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=Path(__file__).with_name('replay_template.html').read_text(encoding='utf-8')
    if template.count('/*__DATA_JSON__*/')!=1:raise ValueError('invalid bundled template placeholder')
    html=template.replace('/*__DATA_JSON__*/',safe_json)
    output_path.write_text(html,encoding='utf-8')
    return output_path


def main(argv=None):
    p=argparse.ArgumentParser(description='Build one browser-only D10 recorded replay; no model execution.')
    p.add_argument('--raw',type=Path,required=True,help='C01 fixtures/test_mixed.csv')
    p.add_argument('--scores',type=Path,required=True,help='C03 if_scores_test.csv')
    p.add_argument('--manifest',type=Path,required=True,help='C01 scenario_manifest.json')
    p.add_argument('--out',type=Path,required=True,help='Standalone HTML output')
    p.add_argument('--score-source',default='RECORDED_SCORE_CSV',help='Visible provenance label')
    p.add_argument('--expect-baseline',action='store_true',help='Verify exact pinned instructor C03 reference hashes and results')
    args=p.parse_args(argv)
    try:
        result=validate_and_build(args.raw,args.scores,args.manifest,args.score_source)
        if args.expect_baseline:assert_reference_baseline(result)
        render_html(result,args.out)
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as e:
        print('D10_REPLAY_CONTRACT_FAIL:',str(e),file=sys.stderr)
        return 2
    print(f'D10_REPLAY_L0_PASS source={result["source"]} score_source={args.score_source}'
        f' traces={len(result["traces"])} windows=104 valid=100 quality=4'
        f' tp={result["confusion"]["TP"]} fp={result["confusion"]["FP"]}'
        f' fn={result["confusion"]["FN"]} tn={result["confusion"]["TN"]}'
        f' raw_sha256={result["raw_sha256"]} scores_sha256={result["scores_sha256"]}'
        f' ros_actual=false gazebo_actual=false browser_not_yet_tested=true')
    print('D10_REPLAY_OUTPUT='+str(args.out.resolve()))
    return 0

if __name__=='__main__':raise SystemExit(main())
