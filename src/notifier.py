import requests


def notify_discord(scraping_results: list[str], hook_url: str):
    for message in scraping_results:
        payload = {"content": message}
        requests.post(hook_url, json=payload, timeout=10)