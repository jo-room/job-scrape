import os
import sys
import json
import datetime
import boto3
import argparse
import tempfile
from tempfile import mkdtemp
from dataclasses import asdict

from selenium import webdriver

from models import *
from job_scrape import get_new_relevant_jobs, format_new_jobs_message, format_errors_message, get_companies, import_from_path

def lambda_handler(event, context, local=False):
    print("event", event)
    limit_company = event["limit_company"] if "limit_company" in event else None
    # defaulting to 2 sec on the lambda
    default_sleep = event["default_sleep"] if "default_sleep" in event else 2
    temp_term = event["temp_term"] if "temp_term" in event else None
    dont_replace_existing = event["dont_replace_existing"] if "dont_replace_existing" in event else False
    dont_write_existing = event["dont_write_existing"] if "dont_write_existing" in event else False

    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    if not local:
        service = webdriver.ChromeService("/opt/chromedriver")
        options.binary_location = '/opt/chrome/chrome'

    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-features=OptimizationGuideModelDownloading")

    if local:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Chrome(options=options, service=service)
    
    # Restrict session permissions to only access user resources
    username = event["aws_config"]["username"]
    sts = boto3.client('sts')
    assumed_role_object = sts.assume_role(
        RoleArn=event["aws_config"]["execution_role_arn"],
        RoleSessionName="role-session" + username,
        Policy=get_inline_session_policy(event["aws_config"]["bucket_name"], username, event["aws_config"]["sns_topic_arn"]),
        DurationSeconds=1000
    )
    credentials = assumed_role_object['Credentials']
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )


    s3 = session.resource('s3')
    bucket = s3.Bucket(event["aws_config"]["bucket_name"])

    if "config_json" in event["aws_config"]:
        config_object = s3.Object(event["aws_config"]["bucket_name"], event["aws_config"]["config_json"])
        config_file_content = config_object.get()['Body'].read().decode('utf-8')
        config = json.loads(config_file_content)
        companies = get_companies(config["companies"])
        search_terms = config["search_terms"]
    else:
        with tempfile.TemporaryDirectory() as tmp_config_scrapers_folder:
            config_path = os.path.join(tmp_config_scrapers_folder, 'config.py')
            scrapers_path = os.path.join(tmp_config_scrapers_folder, 'scrapers.py')
            bucket.download_file(event["aws_config"]["config_file"], config_path)
            bucket.download_file(event["aws_config"]["scrapers_file"], scrapers_path)

            # This is not actually in any way foolproof security, but a sanity check
            assert_no_boto(config_path)
            assert_no_boto(scrapers_path)

            config_module = import_from_path("config", config_path)
            scrapers_module = import_from_path("scrapers", scrapers_path)
            companies = [Company(**company) for company in config_module.get_companies(scrapers_module)]
            search_terms = config_module.search_terms

    run_record_object = s3.Object(event["aws_config"]["bucket_name"], event["aws_config"]["run_record_json"])
    file_content = run_record_object.get()['Body'].read().decode('utf-8')
    run_record = RunRecord.from_dict(json.loads(file_content))

    new_relevant_jobs, run_record, verify_no_jobs, errors_message = get_new_relevant_jobs(
        driver,
        run_record,
        companies,
        search_terms,
        limit_company,
        temp_term,
        default_sleep
    )
    return_message = {}
    
    sns = session.client('sns')

    if len(new_relevant_jobs) > 0:
        new_jobs_message = format_new_jobs_message(new_relevant_jobs)

        response = sns.publish(
            TopicArn=event["aws_config"]["sns_topic_arn"],
            Message=new_jobs_message,
            Subject='New jobs',
        )
        print("New jobs:")
        print(new_jobs_message)
        return_message["new_jobs"] = new_jobs_message
    else:
        print("No new jobs")

    if len(run_record.errors) > 0:
        print(errors_message)
        return_message["errors"] = errors_message
    if run_record.has_new_error():
        response = sns.publish(
            TopicArn=event["aws_config"]["sns_topic_arn"],
            Message=errors_message,
            Subject='New scrape error(s)',
        )

    if dont_replace_existing:
        path, extension = os.path.splitext(event["aws_config"]["run_record_json"])
        run_record_object = s3.Object(event["aws_config"]["bucket_name"], f"{path}_{str(datetime.datetime.now()).replace(" ", "_")}{extension}")
    if not dont_write_existing:
        run_record_object.put(Body=json.dumps(asdict(run_record), indent=4))

    print("finished")
    return {
        'statusCode': 200,
        'body': return_message
    }

def assert_no_boto(file_path):
    with open(file_path) as f:
        assert "boto" not in f.read()

def get_inline_session_policy(bucket_name, username, sns_topic_arn):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "s3:ListBucket"
                ],
                "Effect": "Allow",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}"
                ],
                "Condition": {
                    "StringLike": {
                        "s3:prefix": [
                            f"{username}/*"
                        ]
                    }
                }
            },
            {
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Effect": "Allow",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/{username}/*"
                ]
            },
            {
                "Action": "sns:Publish",
                "Effect": "Allow",
                "Resource": f"{sns_topic_arn}"
            }
        ]
    }
    policy_json = json.dumps(policy)
    return policy_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run with aws resources to scrape new jobs and notify.')
    parser.add_argument('event_json', type=str, help="""Path to lambda event json. Expected structure:
{
    "aws_config": {
        "bucket_name": "",
        "config_file": "",
        "scrapers_file": "",
        "run_record_json": "",
        "sns_topic_arn": "",
    }
    "limit_company": "",
    "default_sleep": 2,
    "dont_replace_existing": true/false,
    "dont_write_existing": true/false
}
        """)

    args = parser.parse_args()

    with open(args.event_json) as f:
        lambda_event = json.load(f)
        lambda_handler(
            lambda_event,
            context=None,
            local=True
        )