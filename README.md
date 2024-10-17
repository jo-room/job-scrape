# Careers Page Scraper

For monitoring the careers page of specific companies. Requires knowing the specific companies you want to follow, and writing scrapers for their careers page.

Can be run as a local Python script to output new jobs (relative to the last run) matching your search terms. Or, can be hosted on AWS to run e.g. daily and send an email notification for new jobs.


## Local development and running

Install dependencies
```sh
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

Create initial files
```sh
mkdir output
echo "{\"existing_jobs\": {}, \"errors\": []}" >> data/run_record.json

mkdir configs
cp example_config.py configs/config.py
cp example_scrapers.py configs/scrapers.py
```

Usage
```sh
source .venv/bin/activate

# Search all companies in config
python3 jobscrape.py configs/ data/run_record.json

# Limit search to company name
python3 jobscrape.py configs/ data/run_record.json --limit_company "example company name"

# Run headless (i.e. without opening Chrome)
python3 jobscrape.py configs/ data/run_record.json --headless
```

Configure `config.py` and write scrapers in `scrapers.py`.


## AWS Lambda + SNS notifications

For local development with the AWS integrations, the entry script is `lambda_function.py`. This is set up to:
1) Dynamically pull the `config.py` and `scrapers.py` files from s3
2) Compare the scraped jobs to a file of existing jobs also on s3
3) Send an email notification if new jobs or scrape errors are found

The dynamic pulling is convoluted, but is concretely useful so that:
1) The company config and scrapers can be modified without having to repackage the docker container and redeploy the lambda
2) You can host and run the lambda for non-software-engineer friends who might be down for some Python-writing and HTML. They can self-manage their configuration by uploading files to s3 via the GUI, and not have to deal with git, docker or anything else AWS. You'll want to restrict their permissions and really warn them about cloud services.

`lambda_function.py` can be run locally to develop the AWS integrations. However, note that a local run of `lambda_function.py` will still pull the `config.py` and `scrapers.py` files from s3 and __will not__ use your local repo copies.

Set up:
- Create a bucket, upload `config.py` and `scrapers.py`, and initialize `run_record.json` with `{"existing_jobs": {}, "errors": []}`
- Build docker image and push to a private ECR repo
- Deploy to a lambda with 2048 MB memory, 512 MB ephemeral storage, and a 10min timeout. Include some retries because the lambda run can be flaky (https://github.com/umihico/docker-selenium-lambda/issues/246). Grant permissions to s3 locations and SNS.
- Configure SNS topic with email notifications
- Configure EventBridge schedule, e.g. 4am daily via cron `0 4 ? * * *`. Target the lambda and configure the payload with a structure as below.
    ```
    {
        "aws_config": {
            "bucket_name": "",
            "config_file": "", // path to config.py within bucket
            "scrapers_file": "", // path to scrapers.py within bucket
            "run_record_json": "", // path within bucket, initialized with `{"existing_jobs": {}, "errors": []}`
            "sns_topic_arn": "",
        }
    }
    ```
- Would be nice to IaC this

The lambda will also send a notification for scraping errors if a notification for that company erroring has not already been sent. A successful scrape for a company will trigger notifications for new errors in the future. I.e., if the scrape if flaky you will get emails for every non-consecutive flake.

See `lambda_function.py` main for additional optional event keys for debugging/dev.


## Programming 102/tips on writing scrapers

For said non-software-engineer friends

Add `breakpoint()` in a scraper to pause there and poke around. E.g., 
```py
job_elements = driver.find_element(By.TAG_NAME, 'main').find_elements(By.TAG_NAME, "li")
breakpoint()

# Run the script
# When it pauses, I can type `job_elements` to check its value. E.g., am I even retrieving anything?
job_elements
# Might output something like
[]
# Meaning that it didn't get anything!
```

A `JobPosting` requires a `title` and `id`.
```py
JobPosting(
    title=job.text, # Doesn't only need to be the title. Can be all the text you want to include in the email or search for relevance in. If it's easier to grab more excess text, just grab more excess text.
    id=link_url, # Should uniquely identify a posting within a given company. A job is only considered "new" if it has a different ID from any other ID seen for this company before.
    link=link_url, # This line is optional. If it's hard to get, you can just delete this line. If provided it will be included in the email. If not, when you get the email you can manually check the company careers page.
)
```

```sh
# Sound notification when done
python3 jobscrape.py configs/ data/run_record.json && say "done"

# Temporarily include an additional search term to verify that the scraper was successfully able to grab jobs on the page (even if none currently are relevant)
python3 jobscrape.py configs/ data/run_record.json --additional_search_term "director"

# Combine limiting to one company (that you are writing the scraper for) and including an additional temporary search term
python3 jobscrape.py configs/ data/run_record.json --limit_company "example company name" --additional_search_term "director"

# Combine with not overwriting the existing jobs file, so that you can keep running the same command to test if the scraper works. There should be a new file with the timestamp in outputs/ that includes the found new director job
python3 jobscrape.py configs/ data/run_record.json --limit_company "example company name" --additional_search_term "director" --dont_replace_existing
```

Selenium documentation:
https://www.selenium.dev/documentation/webdriver/elements/locators/

`.find_element(...)` will error if no element is found.
`.find_elements(...)` (note the plural) will happily keep going if no element(s) are found. If you have a loop through the elements after, it will just not loop through anything.

If you get an error message, search it up.


## Acknowledgements

- https://github.com/MarcusKyung/careers-page-scraper
- https://github.com/umihico/docker-selenium-lambda
