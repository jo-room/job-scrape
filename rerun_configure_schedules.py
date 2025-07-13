"""
After running cloudformation, run this to re-override with user configurations
"""

import boto3
import argparse
import botocore
import datetime

from lambda_configure_schedule import update_schedule_from_config
from models import bcolors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Re-create scheduleConfig.json objects to thus re-trigger configuration lambda"
    )
    parser.add_argument(
        "--usernames",
        type=str,
        required=True,
        help="Comma-delimited string to usernames to re-trigger configuration for",
    )
    parser.add_argument("--bucket_name", type=str, required=True, help="Name of bucket")

    args = parser.parse_args()
    usernames = args.usernames.split(",")

    s3 = boto3.client("s3")

    for username in usernames:
        key = f"{username}/scheduleConfig.json"
        try:
            s3.head_object(Bucket=args.bucket_name, Key=key)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print(
                    bcolors.OKBLUE
                    + f"{username} schedule config not found"
                    + bcolors.ENDC
                )
                continue
            else:
                raise e

        succeeded = update_schedule_from_config(
            args.bucket_name, key, should_email=False
        )
        if succeeded:
            print(bcolors.OKGREEN + f"{username} updated" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + f"{username} errored" + bcolors.ENDC)
