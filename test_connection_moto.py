import boto3
from moto import mock_aws

@mock_aws
def main():
    s3 = boto3.client("s3", region_name="ap-south-1")

    s3.create_bucket(
        Bucket="cost-monitor-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
    )

    response = s3.list_buckets()

    print("Connected to mocked AWS (Moto). Buckets found:")
    for bucket in response["Buckets"]:
        print(f"  - {bucket['Name']}")

if __name__ == "__main__":
    main()