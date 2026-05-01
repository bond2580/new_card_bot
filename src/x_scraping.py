import requests
import re
import os
from datetime import datetime, timezone, timedelta

from dynamodb import is_notified, mark_as_notified, trim_table_to_20


BEARER_TOKEN  = os.environ.get("BEARER_TOKEN")
USER_NAMES    = ["YuGiOh_OCG_INFO", "yu_gi_oh_jp"]
LOOKBACK_MINUTES = 1440  # 直近何分のツイートを取得するか（EventBridgeが毎日21:07実行のため24時間）
USER_IDS = [
    os.environ.get("X_USER_ID_OFFICIAL"),
    os.environ.get("X_USER_ID_JP"),
]
KEY_WORD     = ["カード公開", "再録", "付録", "新カード", "カードを公開", "新たな", "新テーマ"]
NG_WORD      = ["実物", "ラッシュデュエル", "カードを収録", "発売中"]


def build_search_query():
    """Recent Search API用の検索クエリを構築する"""
    user_filter    = " OR ".join([f"from:{name}" for name in USER_NAMES])
    keyword_filter = " OR ".join(KEY_WORD)
    ng_filter      = " ".join([f"-{word}" for word in NG_WORD])
    return f"({user_filter}) ({keyword_filter}) {ng_filter} -is:retweet"


def _start_time_iso() -> str:
    """現在時刻からLOOKBACK_MINUTES分前のISO8601文字列を返す"""
    start = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


def search_recent_tweets(max_results=20) -> dict:
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": build_search_query(),
        "max_results": max_results,
        "tweet.fields": "created_at,text,id,author_id",
        "expansions": "author_id",
        "user.fields": "username",
        "start_time": _start_time_iso(),
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_user_timeline(user_id, max_results=20) -> dict:
    """User Timeline APIでユーザーの最新ツイートを取得する"""
    url = f"https://api.x.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,text,id,author_id",
        "expansions": "author_id",
        "user.fields": "username",
        "exclude": "retweets",
        "start_time": _start_time_iso(),
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def filter_by_keywords(tweets):
    """ツイートリストからキーワード/NGワードでフィルタリングする"""
    filtered = []
    for tweet in tweets:
        text = tweet["text"]
        has_keyword = any(kw in text for kw in KEY_WORD)
        has_ng_word = any(ng in text for ng in NG_WORD)
        if has_keyword and not has_ng_word:
            filtered.append(tweet)
    return filtered


def merge_responses(search_resp, timeline_resps):
    """Recent Search APIとUser Timeline APIの結果をマージし、tweet IDで重複排除する"""
    merged_data = {}
    merged_users = {}

    for resp in [search_resp] + timeline_resps:
        if "data" in resp:
            for tweet in resp["data"]:
                merged_data[tweet["id"]] = tweet
        if "includes" in resp and "users" in resp["includes"]:
            for user in resp["includes"]["users"]:
                merged_users[user["id"]] = user

    result = {}
    if merged_data:
        result["data"] = list(merged_data.values())
    if merged_users:
        result["includes"] = {"users": list(merged_users.values())}
    return result


def process_tweets(response):
    """検索結果からカード情報を抽出し、未通知のものを返す"""
    result = {"messages": [], "card_name": []}

    if "data" not in response:
        return result

    # author_id → username のマッピングを作成
    user_map = {}
    if "includes" in response and "users" in response["includes"]:
        for user in response["includes"]["users"]:
            user_map[user["id"]] = user["username"]

    for tweet in response["data"]:
        user_name = user_map.get(tweet["author_id"], "unknown")
        tweet_url = f"https://x.com/{user_name}/status/{tweet['id']}"

        card_name = re.search(r"◤(.*?)◢", tweet["text"])
        card_name = card_name.group(1) if card_name else "カード公開"
        # 確認用
        print(card_name, tweet_url)

        # DBに登録
        if is_notified(tweet_url) is False:
            mark_as_notified(tweet_url)
            trim_table_to_20()
            result["messages"].append(tweet_url)
            result["card_name"].append(card_name)

    return result


def run_scraper():
    search_resp = search_recent_tweets()
    if "data" in search_resp:
        search_resp["data"] = filter_by_keywords(search_resp["data"])

    timeline_resps = []
    for user_id in USER_IDS:
        if user_id:
            resp = get_user_timeline(user_id)
            if "data" in resp:
                resp["data"] = filter_by_keywords(resp["data"])
            timeline_resps.append(resp)

    merged = merge_responses(search_resp, timeline_resps)
    return process_tweets(merged)


if __name__ == "__main__":
    print(run_scraper())
