import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from dynamodb import is_notified, mark_as_notified, trim_table_to_20

KEY_WORD    = ["収録", "再録", "付録"]
BASE_URL    = "https://yu-gi-oh.jp/"
TARGET_URL  = "https://yu-gi-oh.jp/"  # Lambda の環境変数で設定

# ★ EC2 の Elastic IP を設定（例）
PROXY_SERVER = os.environ.get("PROXY_SERVER")

# -----------------------------
# HTML取得（Cloudflare対策 + プロキシ）
# -----------------------------


def fetch_html_playwright(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": PROXY_SERVER},  # ★ プロキシ設定
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--single-process",
                "--no-zygote"
            ]
        )

        page = browser.new_page()

        # ★ Cloudflare 対策：本物の Chrome UA を使用
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
        })

        page.goto(url, timeout=60000)
        html = page.content()
        browser.close()
        return html


# -----------------------------
# box1 の抽出
# -----------------------------
def extract_box1(html: str):
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("div", class_="box1")


# -----------------------------
# box1 内の data-content 抽出
# -----------------------------
def extract_data_content(box):
    data = box.find("div", class_="data-content")

    if data:
        text = data.get_text(strip=True)
        is_include_new_card = any([key in text for key in KEY_WORD])
        if is_include_new_card:
            return text
    return ""


# -----------------------------
# box1 内のリンク抽出（相対URL → 絶対URL）
# -----------------------------
def extract_link(box):
    a = box.find("a", href=True)
    if not a:
        return None
    return urljoin(BASE_URL, a["href"])


# -----------------------------
# メイン処理
# -----------------------------
def run_scraper():
    try:
        html = fetch_html_playwright(TARGET_URL)
        # print(html[:500])
        boxes = extract_box1(html)

        if not boxes:
            print("box1 が見つかりませんでした")
            return {"status": "no box1"}

        results = []

        for box in boxes:
            text = extract_data_content(box)
            link = extract_link(box)
            print(text, link)

            if text and link:
                # 通知済みでない新規情報の場合
                if not is_notified(link):
                    mark_as_notified(link)
                    # レコードが20件を超えないようにする
                    trim_table_to_20()
                    msg = f"【更新情報】\n{text}\n{link}"
                    results.append(msg)

        return {
            "status": "success",
            "count": len(results),
            "messages": results
        }

    except Exception as e:
        print(f"エラー発生: {str(e)}")
        return {"status": "error", "message": str(e)}


if __name__ == '__main__':
    html = fetch_html_playwright(TARGET_URL)
    print(html)
