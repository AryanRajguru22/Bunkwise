"""Capture the application screenshots used in the final project report.

Starts nothing itself: run the app first (it must be listening on the given URL), then

    python docs/capture_screenshots.py [http://localhost:8501]

Needs Playwright and Microsoft Edge (or pass another Chromium channel via BROWSER_CHANNEL).
Writes PNG files to docs/report_assets/.  These are real renders of the unmodified app.
"""
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "report_assets")
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
CHANNEL = os.environ.get("BROWSER_CHANNEL", "msedge")


def settle(page):
    """Wait until Streamlit has finished running the script and Plotly has drawn."""
    page.wait_for_timeout(1500)
    page.wait_for_selector(".js-plotly-plot .main-svg", timeout=30000)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=30000)
    page.wait_for_timeout(1200)


def shot(page, name, selector=None):
    path = os.path.join(OUT, name)
    if selector:
        page.locator(selector).first.screenshot(path=path)
    else:
        page.screenshot(path=path)
    print("wrote", path)


def crop_overview(path):
    """Keep the header and the three result cards; drop the toolbar strip and the start of the explanation section."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
        top = round(h * 0.04)
        bottom = round(h * 0.865)
        im.crop((0, top, w, bottom)).save(path, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=CHANNEL)
        page = browser.new_page(viewport={"width": 1280, "height": 1500}, device_scale_factor=1.5)
        page.goto(URL)
        settle(page)

        # Default state: attendance 78, credits 2.5, temptation 8
        shot(page, "app_default_top.png", ".stMain")
        crop_overview(os.path.join(OUT, "app_default_top.png"))
        page.get_by_role("tab", name="Aggregation & centroid").click()
        page.wait_for_timeout(1500)
        shot(page, "app_tab_aggregation.png", ".st-key-card-explain")

        # Policy override: attendance 72, credits 2.5, temptation 9
        page.locator("button:has-text('Below 75%, score still high')").first.click()
        settle(page)
        page.get_by_role("tab", name="Fuzzification").click()
        page.wait_for_timeout(800)
        shot(page, "app_override_final.png", ".st-key-card-final-danger")
        browser.close()


if __name__ == "__main__":
    main()
