import requests
import json
import os
import hashlib
import hmac
import base64

LINE_TOKEN          = os.environ.get("LINE_TOKEN")
USER_ID             = os.environ.get("USER_ID")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")


def notify_discord(scraping_results: list[str], hook_url: str):
    for message in scraping_results:
        payload = {"content": message}
        requests.post(hook_url, json=payload, timeout=10)


def notify_linebot(scraping_results: list[str], url: str):
    for message in scraping_results:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        }
        payload = {
            "to": USER_ID,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        requests.post(
            url,
            headers=headers,
            data=json.dumps(payload)
        )


def verify_line_signature(body: str, signature: str) -> bool:
    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(signature, expected)


def reply_linebot(reply_token: str, messages: list[str]):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    line_messages = [{"type": "text", "text": msg[:5000]} for msg in messages[:5]]
    payload = {"replyToken": reply_token, "messages": line_messages}
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        data=json.dumps(payload)
    )


if __name__ == "__main__":
    pass
