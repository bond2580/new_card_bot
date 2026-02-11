import requests
import re
import os

from dynamodb import is_notified, mark_as_notified, trim_table_to_20


BEARER_TOKEN     = os.environ.get("BEARER_TOKEN")
USER_ID_OFFICIAL = os.environ.get("X_USER_ID_OFFICIAL")
USER_ID_JP       = os.environ.get("X_USER_ID_JP")
KEY_WORD         = ["カード公開", "再録", "付録", "新カード", "カードを公開"]
NG_WORD          = ["実物", "ラッシュデュエル"]

USERS = [
    {"user_id": USER_ID_OFFICIAL, "user_name": "YuGiOh_OCG_INFO"},
    {"user_id": USER_ID_JP,       "user_name": "yu_gi_oh_jp"},
]


# ユーザーID取得のために1回だけ実行
def get_user_id(username: str) -> str:
    url = f"https://api.x.com/2/users/by/username/{username}"
    print(BEARER_TOKEN)
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["id"]


def get_latest_tweets(user_id: str, max_results=20) -> dict:
    url = f"https://api.x.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,text,id",
        "exclude": "retweets"
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def filter_tweets_by_keyword(tweets, user_name):

    filter_result = {"messages": [], "card_name": []}

    for tweet in tweets["data"]:
        text = tweet["text"]
        # キーワードがあるかどうか
        isin_kewword = any([keyword in text for keyword in KEY_WORD])
        # NGワードがあるかどうか
        isng         = any([ngword in text for ngword in NG_WORD])

        # キーワードが1つでも含まれているかつNGワードがない場合
        if (isin_kewword is True) & (isng is False):
            tweet_url = f"https://x.com/{user_name}/status/{tweet['id']}"
            card_name = re.search(r"◤(.*?)◢", text)
            card_name = card_name.group(1) if card_name else "カード公開"
            # 確認用
            print(card_name, tweet_url)
            # DBに登録
            if is_notified(tweet_url) is False:
                mark_as_notified(tweet_url)
                trim_table_to_20()
                filter_result["messages"].append(tweet_url)
                filter_result["card_name"].append(card_name)

    return filter_result


def search_tweets(keywords):
    tweets = get_latest_tweets(USER_ID)
    results = []
    for tweet in tweets["data"]:
        text = tweet["text"]
        if any(kw in text for kw in keywords) and not any(ng in text for ng in NG_WORD):
            tweet_url = f"https://x.com/{USER_NAME}/status/{tweet['id']}"
            card_name = re.search(r"◤(.*?)◢", text)
            card_name = card_name.group(1) if card_name else "アンノウン"
            results.append({"card_name": card_name, "url": tweet_url})
    return results


def run_scraper():
    all_results = {"messages": [], "card_name": []}

    for user in USERS:
        tweets = get_latest_tweets(user["user_id"])
        filter_tweets = filter_tweets_by_keyword(tweets, user["user_name"])
        all_results["messages"].extend(filter_tweets["messages"])
        all_results["card_name"].extend(filter_tweets["card_name"])

    return all_results


if __name__ == "__main__":
    print(run_scraper())