import requests
import json
import os

LINE_TOKEN = os.environ.get("LINE_TOKEN")
USER_ID    = os.environ.get("USER_ID")


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


if __name__ == "__main__":
    pass
