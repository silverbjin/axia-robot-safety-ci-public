#!/usr/bin/env python3
"""Browser L1 public fake-score UI: only interaction and render, NO private AE."""
import argparse
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_replay import fake_ae_scores,write_public_smoke_scores
from build_replay import validate_and_build,render_html

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    opt=ap.parse_args()
    opt.output.mkdir(parents=True,exist_ok=True)
    fixture=Path(__import__("os").environ["AXIA_D11_PUBLIC_FIXTURE_DIR"])
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);ifs=d/"if.csv";aes=d/"ae.csv"
        raw=fixture/"test_mixed.csv";man=fixture/"scenario_manifest.json"
        write_public_smoke_scores(raw,man,ifs)
        fake_ae_scores(raw,man,aes)
        payload=validate_and_build(raw,ifs,aes,man,"CI_FAKE_IF","CI_FAKE_AE")
        html=render_html(payload,d/"public_fake_demo.html").read_text(encoding="utf-8")
        with sync_playwright() as p:
            exe=shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
            browser=p.chromium.launch(executable_path=exe if exe else None,channel=None if exe else "chrome",
                                      headless=True,args=["--no-sandbox"])
            page=browser.new_page(viewport={"width":1920,"height":1080},device_scale_factor=1)
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            # file:// direct navigation is not part of this test; Linux page.set_content renders the offline bytes.
            page.set_content(html,wait_until="load")
            assert page.title().startswith("AXIA D11"),page.title()
            assert page.locator("#traceSelect option").count()==14
            assert page.locator("#ifResult").inner_text().find("숨김")>=0
            assert page.locator("#aeResult").inner_text().find("숨김")>=0
            assert page.locator("#truthArea").inner_text().find("숨겨져")>=0
            assert page.locator("#windowStrip .win").count()==10
            page.select_option("#traceSelect",label="TST_A_00 · 신호 관찰")
            for _ in range(4):page.click("#next")
            assert page.locator("#stepWindow").inner_text()=="W4"
            assert page.locator("#truthArea").inner_text().find("숨겨져")>=0
            page.select_option("#guessSelect","WARNING")
            page.click("#showIF")
            assert page.locator("#ifResult").inner_text()=="NORMAL"
            page.click("#showAE")
            assert page.locator("#aeResult").inner_text()=="WARNING"
            page.click("#showTruth")
            assert "합성 이상" in page.locator("#truthArea").inner_text()
            conf=page.locator("#ifConfusion").text_content() or ""
            assert "FP" in conf, ("D11_IF_CONFUSION_VISIBILITY",repr(conf),page.locator("#metricsArea").get_attribute("hidden"))
            page.screenshot(path=str(opt.output/"d11_desktop_1920x1080.png"))
            dims=page.evaluate("({vw:innerWidth,sw:document.documentElement.scrollWidth,charts:[...document.querySelectorAll('canvas')].map(x=>[x.width,x.height])})")
            assert dims["vw"]==1920 and dims["sw"]<=1921,dims
            assert len(dims["charts"])==5 and all(a>0 and b>0 for a,b in dims["charts"]),dims
            # On window transition teacher answers must automatically re-lock.
            page.click("#next")
            assert page.locator("#stepWindow").inner_text()=="W5"
            assert "숨김" in page.locator("#ifResult").inner_text()
            assert "숨김" in page.locator("#aeResult").inner_text()
            assert "숨겨져" in page.locator("#truthArea").inner_text()
            page.click("#showIF");page.click("#showAE")
            assert "NORMAL"==page.locator("#ifResult").inner_text()  # PUBLIC_FAKE_IF, not instructor reference
            assert "NORMAL"==page.locator("#aeResult").inner_text()
            page.click("#resetAnswers")
            assert "숨김" in page.locator("#aeResult").inner_text()
            # Four quality traces are not scored in either model.
            page.select_option("#traceSelect",label="TST_Q_01 · 품질 조사")
            page.click("#showIF");page.click("#showAE");page.click("#showTruth")
            assert "INSUFFICIENT_DATA"==page.locator("#ifResult").inner_text()
            assert "INSUFFICIENT_DATA"==page.locator("#aeResult").inner_text()
            assert page.locator("#ifScore").inner_text()=="UNSCORED"
            assert "SAMPLE_GAP" in page.locator("#truthArea").inner_text()
            assert page.locator("#windowStrip .win").count()==1
            page.set_viewport_size({"width":390,"height":844})
            page.screenshot(path=str(opt.output/"d11_mobile_390x844.png"),full_page=True)
            mobile=page.evaluate("({vw:innerWidth,sw:document.documentElement.scrollWidth})")
            assert mobile["sw"]<=mobile["vw"]+1,mobile
            # Deterministic Play/Pause without wall-clock performance claims.
            page.select_option("#traceSelect",label="TST_A_02 · 신호 관찰")
            page.click("#play")
            assert "일시정지" in page.locator("#play").inner_text()
            page.click("#play")
            assert "재생" in page.locator("#play").inner_text()
            assert not errors,errors
            browser.close()
    print("D11_REPLAY_BROWSER_UI_PASS desktop=1920x1080 mobile=390x844"
          " traces=14 w4_if_normal_ae_warning=true w5_answer_reset=true"
          " quality_unscored=true play_pause=true score_truth_gated=true"
          " private_scores=false ros_actual=false gazebo_actual=false")
    return 0

if __name__=="__main__":raise SystemExit(main())
