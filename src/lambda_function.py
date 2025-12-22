import os
import requests
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# -----------------------------
# 設定
# -----------------------------
BASE_URL = "https://yu-gi-oh.jp/"
TARGET_URL = "https://yu-gi-oh.jp/"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # Lambda の環境変数で設定
KEY_WORD    = ["収録", "再録"]

# -----------------------------
# HTML取得（Cloudflare対策）
# -----------------------------
def fetch_html(url: str) -> str:
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    html = scraper.get(url).text
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
        # テキストに特定のキーワードがあるかどうかチェック
        is_include_new_card = any([key in text for key in KEY_WORD])
        if is_include_new_card:
            return text
    else:
        print("新規の情報なし")
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
# Discord 通知
# -----------------------------
def notify_discord(message: str):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload, timeout=10)


# -----------------------------
# Lambda エントリーポイント
# -----------------------------
def lambda_handler(event, context):
    try:
        html = fetch_html(TARGET_URL)
        boxes = extract_box1(html)

        if not boxes:
            notify_discord("box1 が見つかりませんでした")
            return {"status": "no box1"}

        results = []

        for box in boxes:
            text = extract_data_content(box)
            link = extract_link(box)
            if text & link:
                msg = f"【更新情報】\n{text}\n{link}"
                results.append(msg)
                notify_discord(msg)

        return {
            "status": "success",
            "count": len(results),
            "messages": results
        }

    except Exception as e:
        notify_discord(f"エラー発生: {str(e)}")
        return {"status": "error", "message": str(e)}
    

if __name__ == "__main__":
    # 動作確認用
    response     = fetch_html(TARGET_URL)
    boxes        = extract_box1(response)

    for box in boxes:
        data_content = extract_data_content(box)

        if data_content is True:
            url = extract_link(box)
            notify_discord(url)

    