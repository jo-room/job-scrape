# Careers Page Scraper

Used for:
1. Monitoring the careers page of specific companies. Requires knowing the specific companies you want to follow, and writing scrapers for their careers page.
2. Scraping Crunchbase pages to collect, de-duplicate, and discover companies.

Can be run as a local Python script to output new jobs (relative to the last run) matching your search terms. Or, can be hosted on AWS to run e.g. daily and send an email notification for new jobs.

Crunchbase has a lot of scrape protections and so needs to be run locally.

## Local development and running

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
cp example_files/config.py configs/config.py
cp example_files/scrapers.py configs/scrapers.py
```

Usage
```sh
source .venv/bin/activate

# Search all companies in config
python3 job_scrape.py configs/ data/run_record.json

# Limit search to company name
python3 job_scrape.py configs/ data/run_record.json --limit_company "example company name"

# Run headless (i.e. without opening Chrome)
python3 job_scrape.py configs/ data/run_record.json --headless

# My usual crunchbase run
.venv/bin/python job_scrape.py configs/crunchbase data/crunchbase_run_record.json --backup_run_record
```

Configure `config.py` and write scrapers in `scrapers.py`.

## Deployment

See [docs/deployment.md](docs/deployment.md).

## Using the hosted scraper

See [docs/usage.md](docs/usage.md).

## Acknowledgements

- https://github.com/MarcusKyung/careers-page-scraper
- https://github.com/umihico/docker-selenium-lambda
