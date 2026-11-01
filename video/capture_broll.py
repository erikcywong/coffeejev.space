"""Capture hi-dpi b-roll crops from index.html for the explainer video."""
from __future__ import annotations

import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "video" / "broll"
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ("lab-a", "#lab", "A"),
    ("lab-b", "#lab", "B"),
    ("lab-c", "#lab", "C"),
    ("api", "#api", None),
    ("ledger", "#hitl", None),
    ("econ", "#kpi", None),
    ("chain", "#chain", None),
    ("review", "#review", None),
]


def main() -> None:
    url = (ROOT / "index.html").resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1500, "height": 1200},
                                device_scale_factor=2)
        page.goto(url, wait_until="load")
        page.wait_for_timeout(700)
        for name, selector, tab in TARGETS:
            if tab:
                page.click(f'#labtabs button[data-tab="{tab}"]')
                page.wait_for_timeout(400)
            el = page.locator(selector)
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            el.screenshot(path=str(OUT / f"{name}.png"))
            print("captured", name)
        browser.close()


if __name__ == "__main__":
    main()
