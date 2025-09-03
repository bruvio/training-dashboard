#!/usr/bin/env python3
"""
Render and save a fully loaded web page (with JavaScript executed) using Playwright.
Example:
    python save_rendered_page.py \
        --url http://localhost:8050/activity/4 \
        --output activity_4_rendered.html
"""

import argparse

from playwright.sync_api import sync_playwright


def save_rendered_page(url: str, output: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"[INFO] Loading: {url}")
        page.goto(url)
        # Wait until network is idle (no new requests for 500ms)
        page.wait_for_load_state("networkidle")
        html = page.content()
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[INFO] Saved rendered page to: {output}")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Save a fully rendered webpage as HTML.")
    parser.add_argument("--url", required=True, help="URL of the page to capture.")
    parser.add_argument("--output", default="rendered_page.html", help="Output HTML file (default: rendered_page.html)")
    args = parser.parse_args()
    save_rendered_page(args.url, args.output)


if __name__ == "__main__":
    main()


# python save_rendered_page.py \
#   --url http://localhost:8050/activity/4 \
#   --output activity_4_rendered.html
