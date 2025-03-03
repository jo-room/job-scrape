# Careers Page Scraper

Used for:
1. Job alerts for companies that don't have a way to sign up for job alerts. Requires knowing the specific companies you want to follow, and reusing/writing scrapers for their careers page.
   * See [common_scrapers.py](common_scrapers.py) for the supported types of career pages.
2. Scraping Crunchbase pages to collect, de-duplicate, and discover companies.
   * Crunchbase has a lot of scrape protections and so needs to be run locally (manually triggered, instead of getting emailed when there's something new). It should also be run behind a VPN service, unless you want to risk your home IP getting blocked.

If you're a non-software-engineer friend who's interested in this and might be down for some coding-lite, talk to me 🙂. (Or just talk to me anyway, cos yay friends!)

Can be run as a local Python script to output new jobs (relative to the last run) matching your search terms. Or, can be hosted on AWS to run e.g. daily and send an email notification for new jobs. Only new scrape errors will be printed/emailed; it will not notify if the company also errored in the last run.


## Local development and running

Assumes Python 3.12 and up.

Install dependencies
```sh
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

Create initial files
```sh
mkdir data
cp example_files/initial_run_record.json data/run_record.json

mkdir configs
cp example_files/config.json configs/config.json
```

Usage
```sh
source .venv/bin/activate

# Search all companies in config
python3 job_scrape.py configs/config.json data/run_record.json

# Limit search to company name
python3 job_scrape.py configs/config.json data/run_record.json --limit_company "example company name"

# Include custom scrapers
python3 job_scrape.py configs/config.json data/run_record.json --add_scrapers_file configs/scrapers.py

# Run headless (i.e. without opening Chrome)
python3 job_scrape.py configs/config.json data/run_record.json --headless

# My usual crunchbase run
.venv/bin/python job_scrape.py configs/crunchbase data/crunchbase_run_record.json --backup_run_record
```

## Deployment

See [docs/deployment.md](docs/deployment.md).

## Using the hosted scraper

See [docs/usage.md](docs/usage.md).

## Acknowledgements

- https://github.com/MarcusKyung/careers-page-scraper
- https://github.com/umihico/docker-selenium-lambda
