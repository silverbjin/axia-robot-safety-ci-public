"""C-05 public event wire contract, data-only. No ROS import/control hooks."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path

SOURCE='SYNTHETIC_COURSE_FIXTURE'
TOPIC='/axia/education/diagnostics'
LEVELS={'NORMAL':0,'CAUTION':1,'WARNING':2,'INSUFFICIENT_DATA':3}
REQUIRED={'schema_version','event_id','trace_id','source','source_timestamp_ns','model_id',
          'risk_score','threshold','level','quality_reason','input_sha256',
          'control_authority','certified_estop'}


def validate_event(e):
    if not isinstance(e,dict) or not REQUIRED.issubset(e):raise ValueError('event schema missing')
    if e['schema_version']!=1 or e['source']!=SOURCE or e['level'] not in LEVELS:
        raise ValueError('event source/version/level invalid')
    if not isinstance(e['event_id'],str) or not e['event_id'] or not isinstance(e['trace_id'],str) or not e['trace_id']:
        raise ValueError('event ids invalid')
    if not isinstance(e['model_id'],str) or not e['model_id']:raise ValueError('model_id invalid')
    if type(e['source_timestamp_ns']) is not int or e['source_timestamp_ns']<0:
        raise ValueError('source timestamp invalid')
    if e['control_authority'] is not False or e['certified_estop'] is not False:
        raise ValueError('no control authority; no certified estop')
    if not isinstance(e['input_sha256'],str) or len(e['input_sha256'])!=64 or any(x not in '0123456789abcdef' for x in e['input_sha256']):
        raise ValueError('input digest invalid')
    if e['level']=='INSUFFICIENT_DATA':
        if e['risk_score'] is not None or e['threshold'] is not None or not isinstance(e['quality_reason'],str) or not e['quality_reason']:
            raise ValueError('insufficient data cannot be scored')
    else:
        if e['quality_reason'] not in (None,''):raise ValueError('unexpected quality reason')
        if any(type(e[k]) not in (float,int) or not math.isfinite(e[k]) for k in ('risk_score','threshold')):
            raise ValueError('score nonfinite')
        if e['threshold']<=0:raise ValueError('threshold must be positive for course profile')
    return True


def to_diagnostic_payload(event):
    validate_event(event)
    return {'topic':TOPIC,'level':LEVELS[event['level']],
            'message':'EDUCATION ONLY / NON-CERTIFIED: '+event['level'],
            'hardware_id':'SYNTHETIC_NO_HARDWARE',
            'control_authority':False,'certified_estop':False,
            'event_id':event['event_id'],'source_timestamp_ns':event['source_timestamp_ns'],
            'trace_id':event['trace_id'],'model_id':event['model_id'],
            'risk_score':event['risk_score'],'threshold':event['threshold'],
            'quality_reason':event['quality_reason']}


class EventGate:
    def __init__(self,stale_after_ns=2_000_000_000):
        if stale_after_ns<=0:raise ValueError('invalid stale interval')
        self.stale_after_ns=stale_after_ns
        self.seen=set();self.last_stamps={};self.last_arrival_mono_ns=None

    def accept(self,event,arrival_mono_ns,arrival_wall_ns):
        validate_event(event)
        if type(arrival_mono_ns) is not int or type(arrival_wall_ns) is not int:
            raise ValueError('arrival timestamps invalid')
        if event['event_id'] in self.seen:raise ValueError('duplicate event_id')
        key=(event['model_id'],event['trace_id'])
        ts=event['source_timestamp_ns']
        if key in self.last_stamps and ts<=self.last_stamps[key]:raise ValueError('out_of_order source trace')
        if self.last_arrival_mono_ns is not None and arrival_mono_ns<self.last_arrival_mono_ns:
            raise ValueError('out_of_order arrival monotonic time')
        self.seen.add(event['event_id']);self.last_stamps[key]=ts
        self.last_arrival_mono_ns=arrival_mono_ns
        return True

    def stale(self,now_mono_ns):
        if self.last_arrival_mono_ns is None:return True
        if now_mono_ns<self.last_arrival_mono_ns:raise ValueError('monotonic clock regression')
        # Source timestamp is trace-local; never compare it to wall/monotonic ns.
        return now_mono_ns-self.last_arrival_mono_ns > self.stale_after_ns


def sample_events():
    levels=['NORMAL','CAUTION','WARNING','INSUFFICIENT_DATA']*3
    out=[]
    for i,level in enumerate(levels):
        out.append({'schema_version':1,'event_id':f'DEMO:TST_N_00:{i:03d}',
                    'trace_id':'TST_N_00','source':SOURCE,'source_timestamp_ns':i*100_000_000,
                    'model_id':'EDUCATION_TRANSPORT_DEMO','risk_score':None if level=='INSUFFICIENT_DATA' else [0.1,0.45,0.9][i%4],
                    'threshold':None if level=='INSUFFICIENT_DATA' else 0.5,
                    'level':level,'quality_reason':'DEMO_SAMPLE_MISSING' if level=='INSUFFICIENT_DATA' else None,
                    'input_sha256':'a'*64,'control_authority':False,'certified_estop':False})
    return out


def write_sample_jsonl(path):
    Path(path).write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in sample_events()),encoding='utf-8')
