import requests
import re
import os

from dynamodb import is_notified, mark_as_notified, trim_table_to_20


BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
USER_NAMES   = ["YuGiOh_OCG_INFO", "yu_gi_oh_jp"]
KEY_WORD     = ["カード公開", "再録", "付録", "新カード", "カードを公開"]
NG_WORD      = ["実物", "ラッシュデュエル"]


def build_search_query():
    """Recent Search API用の検索クエリを構築する"""
    user_filter    = " OR ".join([f"from:{name}" for name in USER_NAMES])
    keyword_filter = " OR ".join(KEY_WORD)
    ng_filter      = " ".join([f"-{word}" for word in NG_WORD])
    return f"({user_filter}) ({keyword_filter}) {ng_filter} -is:retweet"


def search_recent_tweets(max_results=20) -> dict:
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": build_search_query(),
        "max_results": max_results,
        "tweet.fields": "created_at,text,id,author_id",
        "expansions": "author_id",
        "user.fields": "username",
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


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
    response = search_recent_tweets()
    return process_tweets(response)


if __name__ == "__main__":
    print(run_scraper())
