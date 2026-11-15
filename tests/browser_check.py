"""Real-browser end-to-end check (NOT part of the unittest suite: needs Playwright + Edge/Chromium).

Start the app first, then:   python tests/browser_check.py [http://localhost:8501]
Set BROWSER_CHANNEL (default msedge; use "chrome" or "" for bundled Chromium).
Every expected value is computed from bunk_meter.evaluate(), so the browser output is compared with the engine.
"""
import os
import re
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import attendance_policy as ap
import bunk_meter as bm

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
CHANNEL = os.environ.get("BROWSER_CHANNEL", "msedge") or None
SIZES = {"desktop": (1280, 900), "tablet": (768, 1024), "mobile": (390, 844)}
SCENARIOS = [("Balanced buffer", 78, 2.5, 8), ("Comfortable, heavy subject", 90, 4, 2),
             ("Low attendance", 50, 4, 3), ("Below 75%, score still high", 72, 2.5, 9),
             ("Easy subject, very safe", 95, 1, 9)]
failures = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def settle(page):
    page.wait_for_selector(".js-plotly-plot .main-svg", timeout=40000)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=30000)
    page.wait_for_timeout(1200)


def body(page):
    return page.inner_text("body")


def no_overflow(page):
    sw, iw = page.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    return sw <= iw


def expect_result(page, att, cred, temp, label):
    ev = bm.evaluate(att, cred, temp)
    try:  # wait for Streamlit's rerun to land: the raw score of THIS input must appear
        page.wait_for_function("t => document.body.innerText.includes(t)", arg=f"{ev.score:.1f} / 100", timeout=15000)
    except Exception:
        pass  # the checks below report the mismatch
    settle(page)
    text = body(page)
    check(f"{ev.score:.1f} / 100" in text, f"{label}: raw score {ev.score:.1f} shown")
    check(ev.final_text in text, f"{label}: final recommendation '{ev.final_text}' shown")
    check(("Below the mandatory 75% attendance" in text) == (att < 75), f"{label}: override banner iff attendance < 75")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=CHANNEL)
        for name, (w, h) in SIZES.items():
            page = browser.new_page(viewport={"width": w, "height": h}, accept_downloads=True)
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(URL)
            settle(page)
            check("BunkWise" in page.title(), f"[{name}] page title")
            check(no_overflow(page), f"[{name}] no horizontal overflow on load")
            expect_result(page, 78, 2.5, 8, f"[{name}] default")

            # sliders: keyboard Home/End on the attendance slider
            sliders = page.get_by_role("slider")
            check(sliders.count() == 3, f"[{name}] three sliders present")
            sliders.nth(0).focus()
            page.keyboard.press("Home")
            settle(page)
            expect_result(page, 0, 2.5, 8, f"[{name}] attendance Home")
            page.keyboard.press("End")
            settle(page)
            expect_result(page, 100, 2.5, 8, f"[{name}] attendance End")
            for _ in range(51):  # 100 -> 74.5 in 0.5 steps
                page.keyboard.press("ArrowLeft")
            settle(page)
            expect_result(page, 74.5, 2.5, 8, f"[{name}] attendance 74.5")
            page.keyboard.press("ArrowRight")
            settle(page)
            expect_result(page, 75, 2.5, 8, f"[{name}] attendance exactly 75")

            # all five scenarios
            page.get_by_text("Try an example scenario").click()
            for label, att, cred, temp in SCENARIOS:
                page.locator("button:visible", has_text=label).first.click()
                settle(page)
                expect_result(page, att, cred, temp, f"[{name}] scenario {label}")
                vals = [sliders.nth(i).input_value() for i in range(3)]
                check([float(v) for v in vals] == [att, cred, temp], f"[{name}] scenario {label} sets sliders {vals}")
                check(no_overflow(page), f"[{name}] scenario {label}: no horizontal overflow")

            # tabs
            for tab in ("What if?", "75% planner", "Compare subjects", "Inside the engine", "Fuzzification", "Active rules",
                        "Aggregation & centroid", "Membership graphs", "About & limits", "Why this result"):
                page.get_by_role("tab", name=tab).first.click()
                page.wait_for_timeout(700)
                check(no_overflow(page), f"[{name}] tab '{tab}': no horizontal overflow")

            # 75% planner: type real counts, compare with the policy module
            page.get_by_role("tab", name="75% planner").first.click()
            page.wait_for_timeout(700)
            for label, value in (("Classes held so far", "300"), ("Classes attended", "225")):
                box = page.get_by_label(label)
                box.fill(value)
                box.press("Enter")
                page.wait_for_timeout(900)
            proj = ap.project(225, 300)
            settle(page)
            check(f"{proj.percent_now:.2f}%" in body(page) and f"{proj.percent_if_skip:.2f}%" in body(page),
                  f"[{name}] planner shows {proj.percent_now:.2f}% now and {proj.percent_if_skip:.2f}% after a skip")
            check("below 75%" in body(page).lower() and not proj.meets_if_skip, f"[{name}] planner warns that a skip breaks 75%")
            check(no_overflow(page), f"[{name}] planner: no horizontal overflow")
            page.get_by_role("tab", name="Why this result").first.click()

            # download report
            with page.expect_download() as dl:
                page.get_by_role("button", name=re.compile("Download decision report")).click()
            target = os.path.join(tempfile.mkdtemp(), "bunkwise_report.md")
            dl.value.save_as(target)
            with open(target, encoding="utf-8") as f:
                report = f.read()
            ev = bm.evaluate(95, 1, 9)
            check(f"{ev.score:.1f} / 100" in report and "not a probability" in report,
                  f"[{name}] downloaded report contains the engine score and the disclaimer")
            check(not errors, f"[{name}] no console errors {errors}")
            page.close()
        browser.close()
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
