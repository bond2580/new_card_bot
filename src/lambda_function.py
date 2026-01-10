import os

from scraper import run_scraper
from notifier import notify_discord
from ec2 import start_ec2, stop_ec2

# -----------------------------
# 設定
# -----------------------------
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # Lambdaの環境変数で設定

# -----------------------------
# Lambda エントリーポイント
# -----------------------------
   
    
def lambda_handler(event, context):

    start_ec2()
    try:
        # Playwright scraper 実行
        status  = run_scraper()
        results = status.get("messages")
        if results:
            notify_discord(results, WEBHOOK_URL)
        else:
            print("新着情報なし")
    finally:
        stop_ec2()


if __name__ == "__main__":
    start_ec2()
    try:
        # Playwright scraper 実行
        status  = run_scraper()
        results = status.get("messages")
        print("結果結果", results)
        if results:
            pass
            # notify_discord(results, WEBHOOK_URL)
        else:
            print("新着情報なし")
    finally:
        stop_ec2()
