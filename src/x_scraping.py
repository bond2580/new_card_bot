import requests
import re
import os

from dynamodb import is_notified, mark_as_notified, trim_table_to_20


BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
USER_ID      = os.environ.get("X_USER_ID")
KEY_WORD     = ["カード公開", "再録", "付録"]
NG_WORD      = ["実物", "ラッシュデュエル"]
USER_NAME    = "YuGiOh_OCG_INFO"

# ユーザーID取得のために1回だけ実行
# def get_user_id(username: str) -> str:
#     url = f"https://api.x.com/2/users/by/username/{username}"
#     headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
#     return response.json()["data"]["id"]


# user_id = get_user_id("YuGiOh_OCG_INFO")
# print("user_id:", user_id)


def get_latest_tweets(user_id: str, max_results=50):
    url = f"https://api.x.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,text,id"
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def filter_tweets_by_keyword(tweets):

    filter_result = {"messages": [], "card_name": []}
    for tweet in tweets["data"]:
        text = tweet["text"]
        # キーワードがあるかどうか
        isin_kewword = any([keyword in text for keyword in KEY_WORD])
        # NGワードがあるかどうか
        isng         = any([ngword in text for ngword in NG_WORD])

        # キーワードが1つでも含まれているかつNGワードがない場合
        if (isin_kewword is True) & (isng is False):
            tweet_url = f"https://x.com/{USER_NAME}/status/{tweet['id']}"
            card_name = re.search(r"◤(.*?)◢", text)
            card_name = card_name.group(1) if card_name else "アンノウン"
            # ログ確認用
            print(card_name, tweet_url)
            # DBに登録
            if not is_notified(tweet_url):
                mark_as_notified(tweet_url)
                trim_table_to_20()
                filter_result["messages"].append(tweet_url)
                filter_result["card_name"].append(card_name)

    return filter_result


def run_scraper():
    tweets        = get_latest_tweets(USER_ID)
    filter_tweets = filter_tweets_by_keyword(tweets)

    return filter_tweets


if __name__ == "__main__":
    print(run_scraper())