import os

from x_scraping import run_scraper
from notifier import notify_discord, notify_linebot

# -----------------------------
# 設定
# -----------------------------
WEBHOOK_URL      = os.environ.get("WEBHOOK_URL")
WEBHOOK_URL_LINE = "https://api.line.me/v2/bot/message/push" # Lambdaの環境変数で設定

# -----------------------------
# Lambda エントリーポイント
# -----------------------------


def lambda_handler(event, context):
    try:
        # Playwright scraper 実行
        status  = run_scraper()
        print(status)
        results = status.get("messages")
        if results:
            notify_discord(results, WEBHOOK_URL)
            notify_linebot(results, WEBHOOK_URL_LINE)
        else:
            print("新着情報なし")
    except Exception as e:
        error_message = [e]
        notify_linebot(error_message, WEBHOOK_URL_LINE)


if __name__ == "__main__":
    # start_ec2()
    try:
        # Playwright scraper 実行
        status  = run_scraper()
        print(status)
        results = status.get("messages")
        print("結果結果", results)
        if results:
            notify_discord(results, WEBHOOK_URL)
            notify_linebot(results, WEBHOOK_URL_LINE)
        else:
            print("新着情報なし")
    finally:
        pass
        # stop_ec2()
