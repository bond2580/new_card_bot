import boto3
from botocore.exceptions import ClientError
from datetime import datetime

DYNAMO_TABLE = "ygo_notified"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMO_TABLE)


# -----------------------------
# すでに通知済みかチェック
# -----------------------------
def is_notified(item_id: str) -> bool:
    try:
        response = table.get_item(Key={"id": item_id})
        return "Item" in response
    except ClientError as e:
        print("DynamoDB get_item error:", e)
        return False


# -----------------------------
# 通知済みとして登録
# -----------------------------
def mark_as_notified(item_id: str):
    try:
        today     = datetime.now()
        timestamp = int(datetime.timestamp(today))
        table.put_item(Item={"id": item_id, "time": timestamp})
    except ClientError as e:
        print("DynamoDB put_item error:", e)


# ------------------------------
# テーブルが20件を超えたら古い順に削除
# ------------------------------

def trim_table_to_20(limit=20):
    items = []
    response = table.scan()

    # ページング対応
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    # ソートキー sk を基準に昇順（古い順）に並べる
    items_sorted = sorted(items, key=lambda x: x["time"])

    # 20件以内なら何もしない
    if len(items_sorted) <= limit:
        print("No trimming needed.")
        return

    # 削除対象（古い順から limit を超えた分）
    to_delete = items_sorted[:-limit]

    # バッチ削除
    with table.batch_writer() as batch:
        for item in to_delete:
            batch.delete_item(
                Key={
                    "id": item["id"]
                }
            )

    print(f"Deleted {len(to_delete)} old items.")


if __name__ == "__main__":
    trim_table_to_20(limit=1)
