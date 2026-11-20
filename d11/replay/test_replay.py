"""AXIA D11 public recorded-UI contracts. Only public synthetic fixture + fake scores."""
import csv, json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from os import environ
from sys import path as syspath

HERE = Path(__file__).resolve().parent
PUBLIC_ROOT = HERE.parents[1]
syspath.insert(0, str(PUBLIC_ROOT / "d10/replay"))
from test_replay import write_public_smoke_scores

def fake_ae_scores(raw, manifest, path):
    """Independent fake UI score, NEVER trained AE and NEVER instructor values."""
    with raw.open(newline="", encoding="utf-8") as f:
        records=list(csv.DictReader(f))
    m=json.loads(manifest.read_text(encoding="utf-8"))
    by={}
    for r in records:by.setdefault(r["trace_id"],[]).append(r)
    columns=("trace_id","window_id","timestamp_ns","status","quality_reason","truth_label","risk_score","threshold","prediction")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=columns,lineterminator="\n");w.writeheader()
        for tid,rows in by.items():
            if tid in m["quality_cases"]:
                w.writerow(dict(trace_id=tid,window_id=0,timestamp_ns=rows[-1]["timestamp_ns"],status="INSUFFICIENT_DATA",
                    quality_reason=m["quality_cases"][tid],truth_label=-1,risk_score="",threshold="",prediction="INSUFFICIENT_DATA"))
            else:
                for wi in range(10):
                    block=rows[wi*10:(wi+1)*10]
                    score=0.8 if tid=="TST_A_00" and wi==4 else 0.2
                    w.writerow(dict(trace_id=tid,window_id=wi,timestamp_ns=block[-1]["timestamp_ns"],
                        status="VALID",quality_reason="",truth_label=block[-1]["truth_label"],
                        risk_score=f"{score:.8f}",threshold="0.50000000",
                        prediction="WARNING" if score>0.5 else "NORMAL"))

class ReplayD11Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=Path(environ["AXIA_D11_PUBLIC_FIXTURE_DIR"])
        cls.raw=fixture/"test_mixed.csv"
        cls.manifest=fixture/"scenario_manifest.json"

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d=Path(self.tmp.name)
        self.ifs=self.d/"if_scores.csv"
        self.aes=self.d/"ae_scores.csv"
        write_public_smoke_scores(self.raw,self.manifest,self.ifs)
        fake_ae_scores(self.raw,self.manifest,self.aes)
        import build_replay as b
        self.mod=b

    def payload(self):
        return self.mod.validate_and_build(self.raw,self.ifs,self.aes,self.manifest,
                                            "CI_FAKE_IF","CI_FAKE_AE")

    def test_joined_window_models_are_independent(self):
        p=self.payload()
        self.assertEqual(len(p["traces"]),14)
        self.assertEqual(sum(len(t["windows"]) for t in p["traces"]),104)
        self.assertEqual(p["models"]["IF"]["threshold"],0.1)
        self.assertEqual(p["models"]["AE"]["threshold"],0.5)
        self.assertNotEqual(p["models"]["IF"]["confusion"],p["models"]["AE"]["confusion"])
        t=next(x for x in p["traces"] if x["id"]=="TST_A_00")
        self.assertEqual(t["windows"][4]["if"]["prediction"],"NORMAL")
        self.assertEqual(t["windows"][4]["ae"]["prediction"],"WARNING")
        self.assertEqual(t["windows"][4]["truth"],1)
        self.assertEqual(p["source"],"SYNTHETIC_COURSE_FIXTURE")
        self.assertFalse(p["ros_actual"]);self.assertFalse(p["gazebo_actual"])
        self.assertFalse(p["safety_control_authority"])

    def test_quality_is_never_scored_by_either_model(self):
        p=self.payload()
        for t in p["traces"]:
            if t["quality_reason"]:
                self.assertEqual(len(t["windows"]),1)
                w=t["windows"][0]
                self.assertEqual(w["status"],"INSUFFICIENT_DATA")
                for name in ("if","ae"):
                    self.assertIsNone(w[name]["score"])
                    self.assertIsNone(w[name]["threshold"])
                    self.assertEqual(w[name]["prediction"],"INSUFFICIENT_DATA")

    def test_join_rejects_ae_timestamp_mismatch(self):
        txt=self.aes.read_text().replace("TST_A_00,4,4900000000","TST_A_00,4,4800000000")
        self.aes.write_text(txt)
        with self.assertRaisesRegex(ValueError,"timestamp"):
            self.payload()

    def test_join_rejects_ae_score_prediction_mismatch(self):
        s=self.aes.read_text().replace("0.80000000,0.50000000,WARNING","0.80000000,0.50000000,NORMAL")
        self.aes.write_text(s)
        with self.assertRaisesRegex(ValueError,"prediction"):
            self.payload()

    def test_join_rejects_invalid_as_normal(self):
        s=self.aes.read_text().replace("INSUFFICIENT_DATA,MISSING_VALUE,-1,,,INSUFFICIENT_DATA",
          "INSUFFICIENT_DATA,MISSING_VALUE,-1,0.00000000,0.50000000,NORMAL")
        self.aes.write_text(s)
        with self.assertRaisesRegex(ValueError,"quality"):
            self.payload()

    def test_render_offline_and_hidden_answers(self):
        out=self.d/"replay.html"
        self.mod.render_html(self.payload(),out)
        data=out.read_text("utf-8")
        for keyword in ('D11','IF 판정 공개','AE 판정 공개','정답·오차 해설 공개',
                        'TST_A_00','INSUFFICIENT_DATA','<canvas','content="default-src'):
            self.assertIn(keyword,data)
        self.assertNotIn('https://',data)
        self.assertNotIn('fetch(',data)
        self.assertNotIn('WebSocket(',data)
        self.assertNotIn('send_goal_async',data)
        self.assertNotIn('<iframe',data)

    def test_generated_js_parses(self):
        node=shutil.which("node")
        self.assertIsNotNone(node)
        out=self.d/"demo.html";self.mod.render_html(self.payload(),out)
        js=out.read_text("utf-8").split("<script>",1)[1].split("</script>",1)[0]
        j=self.d/"demo.js";j.write_text(js,encoding="utf-8")
        p=subprocess.run([node,"--check",str(j)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_scores_not_derived_from_truth_labels(self):
        p=self.payload()
        a=next(t for t in p["traces"] if t["id"]=="TST_A_02")
        self.assertEqual(a["windows"][6]["if"]["prediction"],"WARNING")
        self.assertEqual(a["windows"][6]["ae"]["prediction"],"NORMAL")
        self.assertEqual(a["windows"][6]["truth"],1)
        self.assertEqual(p["models"]["AE"]["score_source"],"CI_FAKE_AE")

if __name__=="__main__": unittest.main()
