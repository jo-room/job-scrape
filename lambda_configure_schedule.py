"""
Lambda function
Triggered by all object create events with suffix `scheduleConfig.json`
Assumes ARN_ROOT lambda environment variable that EXCLUDES a trailing `:`

Currently manually copied to lambda to deploy, then configure the above
"""

import json
import os
import urllib.parse
import boto3
import copy

arn_root = os.environ.get("ARN_ROOT")

s3 = boto3.client("s3")
sns = boto3.client("sns")
scheduler = boto3.client("scheduler")


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    update_schedule_from_config(bucket, key)


def update_schedule_from_config(bucket, key, should_email=True) -> bool:
    assert key.count("/") == 1
    username, file_name = key.split("/")

    file_content = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")

    try:
        config = json.loads(file_content)
    except json.JSONDecodeError as e:
        message = "Error in JSON formatting:\n" + str(e)
        if e.msg == "Expecting property name enclosed in double quotes":
            message += (
                "\n Check if there is a trailing comma, or if there are single quotes."
            )
        print(message)

        if should_email:
            sns.publish(
                TopicArn=f"{arn_root}:job-scrape-{username}",
                Message=message,
                Subject="Error configuring schedule",
            )
        return False

    config_validation_errors = validate_config(config)
    if len(config_validation_errors) > 0:
        message = "Configuration not valid:\n" + "\n".join(config_validation_errors)
        print(message)

        if should_email:
            sns.publish(
                TopicArn=f"{arn_root}:job-scrape-{username}",
                Message=message,
                Subject="Error configuring schedule",
            )
        return False

    schedule = scheduler.get_schedule(
        Name=f"job-scrape-{username}", GroupName="job-scrape"
    )
    schedule_update = copy.deepcopy(schedule)
    for key in ["ResponseMetadata", "Arn", "CreationDate", "LastModificationDate"]:
        del schedule_update[key]

    # default_config = {
    #     "enabled": True,
    #     "hour": 6,
    #     "weekends": False,
    # }

    hours = (
        config["hour"]
        if isinstance(config["hour"], int)
        else ",".join([str(hour) for hour in config["hour"]])
    )
    day = "*" if config["weekends"] else "2-6"
    schedule_update["State"] = "ENABLED" if config["enabled"] else "DISABLED"
    schedule_update["ScheduleExpression"] = f"cron(0 {hours} ? * {day} *)"

    response = scheduler.update_schedule(**schedule_update)
    message = f'Updated {username} schedule to {schedule_update["State"]} on hour {hours} {"including" if config["weekends"] else "excluding"} weekends.'
    print(message)

    if should_email:
        sns.publish(
            TopicArn=f"{arn_root}:job-scrape-{username}",
            Message=message,
            Subject="Schedule has been updated",
        )
    return True


def validate_config(config):
    def validate_hour(hour):
        if not isinstance(hour, int):
            return f'"hour" {hour} must be an integer'
        if hour < 0 or hour > 23:
            return f'"hour" {hour} must be between 0 (midnight) and 23 inclusive'
        return None

    errors = []
    if not (config["enabled"] == True or config["enabled"] == False):
        errors.append('"enabled" must be true or false (lower case, no quotes)')
    if isinstance(config["hour"], list):
        for hour in config["hour"]:
            error = validate_hour(hour)
            if error:
                errors.append(error)
    else:
        error = validate_hour(config["hour"])
        if error:
            errors.append(error)
    if not (config["weekends"] == True or config["weekends"] == False):
        errors.append('"weekends" must be true or false (lower case, no quotes)')
    return errors
