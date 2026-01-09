import boto3
from botocore.exceptions import ClientError

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
        table.put_item(Item={"id": item_id})
    except ClientError as e:
        print("DynamoDB put_item error:", e)

pass