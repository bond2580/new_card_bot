import boto3

EC2_INSTANCE_ID = "i-03886592ffa292cba"


def start_ec2(max_roop=5):
    counter = 0
    for counter in range(max_roop):
        try:
            ec2 = boto3.client("ec2")
            ec2.start_instances(InstanceIds=[EC2_INSTANCE_ID])
            print("EC2 起動中…")

            # 起動完了まで待つ, 成功したらbreak
            waiter = ec2.get_waiter("instance_running")
            waiter.wait(InstanceIds=[EC2_INSTANCE_ID])
            print("EC2 起動完了")
            break
        except Exception as e:
            print(f"EC2起動失敗 ({counter}/{max_roop}回目) {e}")
    
    if counter >= max_roop:
        print(f"EC2起動失敗")
        raise


def stop_ec2():
    ec2 = boto3.client("ec2")
    ec2.stop_instances(InstanceIds=[EC2_INSTANCE_ID])
    print("EC2 停止中…")


if __name__ == "__main__":
    start_ec2()
    stop_ec2()
