# Deployment to AWS Lambda + SNS notifications

Host on AWS to run e.g. daily and send an email notification for new jobs. Allows users to self-manage the companies they want to scrape, and the scraping schedule.

## System design

For local development with the AWS integrations, the entry script is `lambda_function.py`. This is set up to:
1) Dynamically pull the `config.py` and `scrapers.py` files from s3
2) Compare the scraped jobs to a file of existing jobs also on s3
3) Send an email notification if new jobs or scrape errors are found

The dynamic pulling is convoluted, but is concretely useful so that:
1) The company config and scrapers can be modified without having to repackage the docker container and redeploy the lambda
2) You can host and run the lambda for non-software-engineer friends who might be down for some Python-writing and HTML. They can self-manage their configuration by uploading files to s3 via the GUI, and not have to deal with git, docker or anything else AWS. You'll want to restrict their permissions and really warn them about cloud services. See the `deploy/` folder for some tools.

`lambda_function.py` can be run locally to develop the AWS integrations. However, note that a local run of `lambda_function.py` will still pull the `config.py` and `scrapers.py` files from s3 and __will not__ use your local repo copies.

See `lambda_function.py` main for additional optional event keys for debugging/dev.

## Devops set up (assuming multiple users)
- Run the cloudformation template (`deploy/cloudformationTemplate.yaml`) with a comma-delimited list of usernames
- Create a bucket. Within folder(s) for the username(s), upload `config.py`, `scrapers.py`, and an initial `run_record.json` with `{"existing_jobs": {}, "errors": []}`
- Create a lambda with 2048 MB memory, 512 MB ephemeral storage, and a 10min timeout. Include some retries because the lambda run can be flaky (https://github.com/umihico/docker-selenium-lambda/issues/246). Grant permissions to the bucket and SNS.
- Set up Github Actions with the appropriate secrets. It will build the docker image, push to ECR, and deploy to the lambda.
- For each SNS Topic created by the cloudformation, add a Subscription to an email
- Create IAM accounts/roles for friend log in (see `deploy/IAM role for friends.json` for restricted permissions)

The lambda will also send a notification for scraping errors if a notification for that company erroring has not already been sent. A successful scrape for a company will trigger notifications for new errors in the future. I.e., if the scrape if flaky you will get emails for every non-consecutive flake.

## For users to self-configure the lambda schedule
So that users can enable/disable their email notifications without going through you.

- Deploy `lambda_configure_schedule.py` to a lambda.
- Users should upload a `scheduleConfig.json` (see `example_files/`) to their bucket folder. The interface is deliberately limited so that users don't accidentally write CRON expressions that fire every second. This file is optional, the schedule otherwise defaults to the cloudformation template.
- Running the cloudformation template will override prior user configurations. To re-implement user configurations, run `rerun_configure_schedules.py` locally.
