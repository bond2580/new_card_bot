import os
import json

from x_scraping import run_scraper
from notifier import notify_discord, notify_linebot, verify_line_signature, reply_linebot
from dynamodb import get_recent_urls

# -----------------------------
# 設定
# -----------------------------
WEBHOOK_URL      = os.environ.get("WEBHOOK_URL")
WEBHOOK_URL_LINE = "https://api.line.me/v2/bot/message/push"

# -----------------------------
# Lambda エントリーポイント
# -----------------------------


def lambda_handler(event, context):
    if "httpMethod" in event or "requestContext" in event:
        return handle_api_gateway_event(event)
    else:
        return handle_scheduled_event(event)


# -----------------------------
# EventBridge スケジュール実行（既存ロジック）
# -----------------------------


def handle_scheduled_event(event):
    try:
        status = run_scraper()
        print(status)
        results = status.get("messages")
        if results:
            notify_discord(results, WEBHOOK_URL)
            notify_linebot(results, WEBHOOK_URL_LINE)
        else:
            print("新着情報なし")
    except Exception as e:
        error_message = [str(e)]
        notify_linebot(error_message, WEBHOOK_URL_LINE)


# -----------------------------
# API Gateway（LINE Webhook）
# -----------------------------


def handle_api_gateway_event(event):
    # ヘッダーから署名を取得（API Gatewayはヘッダー名を小文字にする場合がある）
    headers = event.get("headers", {})
    signature = headers.get("x-line-signature") or headers.get("X-Line-Signature", "")

    body = event.get("body", "")

    # 署名検証
    if not verify_line_signature(body, signature):
        print("署名検証失敗")
        return {"statusCode": 403, "body": "Invalid signature"}

    body_json = json.loads(body)
    events = body_json.get("events", [])

    # LINE Webhook検証リクエスト（eventsが空）
    if not events:
        return {"statusCode": 200, "body": "OK"}

    for line_event in events:
        if line_event.get("type") != "message":
            continue
        if line_event.get("message", {}).get("type") != "text":
            continue

        reply_token = line_event["replyToken"]

        try:
            urls = get_recent_urls(days=3)
            if urls:
                messages = ["直近3日間の新着カード情報:"]
                messages.extend(urls)
                reply_linebot(reply_token, messages)
            else:
                reply_linebot(reply_token, ["直近3日間の新着情報はありません。"])
        except Exception as e:
            print(f"DB取得エラー: {e}")
            reply_linebot(reply_token, ["情報の取得中にエラーが発生しました。"])

    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    try:
        status = run_scraper()
        print(status)
        results = status.get("messages")
        print("結果", results)
        if results:
            notify_discord(results, WEBHOOK_URL)
            notify_linebot(results, WEBHOOK_URL_LINE)
        else:
            print("新着情報なし")
    finally:
        pass
