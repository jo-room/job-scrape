#! /usr/bin/env python3
# Need selenium because postings might take js to load

import argparse
import datetime
import traceback
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from tempfile import mkdtemp

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from models import *

def get_new_relevant_jobs(driver, run_record: RunRecord, limit_company = None, additional_search_term = None, default_sleep = 1):
    existing_jobs = defaultdict(set, {key: set(value) for key, value in run_record.existing_jobs.items()})

    relevant_jobs, skipped_companies, verify_no_jobs, errors = get_relevant_jobs(driver, limit_company, additional_search_term, default_sleep)
    new_relevant_jobs = {}

    # Group jobs by company, and update existing
    for company, job in relevant_jobs:
        if job.id not in existing_jobs[company.name]:
            if company.name in new_relevant_jobs:
                new_relevant_jobs[company.name]["jobs"].append(job)
            else:
                new_relevant_jobs[company.name] = {
                    "company": company,
                    "jobs": [job]
                }

            existing_jobs[company.name].add(job.id)

    existing_jobs = {key: sorted(list(value)) for key, value in existing_jobs.items()}


    # Annotate if errors are new, and create new run record
    prior_run_errors_company_names = {error.company_name for error in run_record.errors}

    errors_message = None
    scrape_errors = []

    if len(errors) > 0:
        messages = []

        for company, error in errors:
            is_new_this_run = company.name not in prior_run_errors_company_names
            scrape_error = ScrapeError(
                company_name=company.name,
                jobs_page=company.jobs_page,
                message=str(error),
                is_new_this_run=is_new_this_run
            )
            scrape_errors.append(scrape_error)
            messages.append(f"{"NEW ERROR " if is_new_this_run else ""}{company.name}{f" ({company.name}, {company.jobs_page})" if {company.name} else ""}: {getattr(error, 'msg', repr(error))}\n{''.join(traceback.format_exception(error))}")

        errors_message = "Errors:\n" + "\n".join(messages)

    run_record = RunRecord(existing_jobs, scrape_errors)            

    return new_relevant_jobs, run_record, verify_no_jobs, errors_message

def get_relevant_jobs(driver, limit_company, additional_search_term, default_sleep):
    relevant_jobs: list[tuple[Company, list[JobPosting]]] = []
    skipped_companies = []
    verify_no_jobs = []
    errors: list[tuple[Company, Exception]] = []

    # Dynamic import so that we can e.g. dynamically pull this file from s3, and change the config without repackaging the docker image
    import config
    companies = [Company(**company) for company in config.companies]

    search_terms = config.search_terms
    if additional_search_term:
        search_terms.append(additional_search_term)

    for company in companies:
        if limit_company and limit_company.lower() not in company.name.lower():
            continue
        
        if company.active:
            assert company.jobs_page
            print("Checking", company.name)
            try:
                company_relevant_jobs, jobs_page_status = get_company_relevant_jobs(driver, company, search_terms, default_sleep)
                if len(company_relevant_jobs) > 0:
                    for job in company_relevant_jobs:
                        relevant_jobs.append((company, job))
                elif jobs_page_status in {JobsPageStatus.GENERIC_NO_JOBS_PHRASE_FOUND, JobsPageStatus.NO_JOBS_PHRASE_NOT_FOUND_BUT_NO_JOBS}:
                    verify_no_jobs.append(company)
            except Exception as e:
                errors.append((company, e))
        
        else:
            skipped_companies.append(company.name)
    
    driver.close()  # Close the original browser window
    return relevant_jobs, skipped_companies, verify_no_jobs, errors

def get_company_relevant_jobs(driver, company, search_terms, default_sleep) -> (list[JobPosting], JobsPageStatus):
    driver.get(company.jobs_page)
    time.sleep(company.load_sleep if company.load_sleep else default_sleep)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to bottom to lazy load everything
    time.sleep(company.scroll_sleep if company.scroll_sleep else default_sleep)

    company_has_jobs, jobs_page_status = has_jobs(driver, company)
    if company_has_jobs:
        if "Verify you are human" in driver.find_element(By.TAG_NAME, 'body').text:
            raise Exception(f"Human verification hit. There are probably ways to bypass but I haven't figured/built that out yet. Text: {driver.find_element(By.TAG_NAME, 'body').text.replace("\n", " ")}")
        if company.jobs_page_class:
            jobs = company.jobs_page_class.get_jobs(driver)
            if len(jobs) > 0:
                jobs_page_status = JobsPageStatus.SOME_JOB_FOUND
            relevant_jobs = [job for job in jobs if title_is_relevant(company, job.title, search_terms)]
        else:
            raise Exception(f"Scrape not implemented. Body text: {driver.find_element(By.TAG_NAME, 'body').text.replace("\n", " ")}")
    else:
        return [], jobs_page_status

    return relevant_jobs, jobs_page_status

def has_jobs(driver, company) -> (bool, JobsPageStatus):
    all_text_lower = driver.find_element(By.TAG_NAME, 'body').text.lower()
    if all_text_lower is None or all_text_lower == "":
        raise Exception(company.name + ": Error retrieving text")
    if company.no_jobs_phrase:
        if company.no_jobs_phrase.lower() in all_text_lower:
            return False, JobsPageStatus.SPECIFIC_NO_JOBS_PHRASE_FOUND
        return True, JobsPageStatus.NO_JOBS_PHRASE_NOT_FOUND_BUT_NO_JOBS
    
    return True, JobsPageStatus.NO_JOBS_FOUND

def title_is_relevant(company, title, search_terms) -> bool:
    if company.relevant_search_terms:
        return any(search_term.lower() in title.lower() for search_term in company.relevant_search_terms)

    return any(search_term.lower() in title.lower() for search_term in search_terms)

def format_new_jobs_message(new_jobs: dict[str, dict[str, any]]) -> str:
    message = ""
    for company_name, info in new_jobs.items():
        message += f"\n{company_name} ({info["company"].jobs_page}):\n"
        for job in info["jobs"]:
                message += f"\t {job.title.replace("\n", " ")} {job.link if job.link else ""}\n"
    return message

def format_errors_message(errors: list[ScrapeError]) -> str:
    if len(errors) > 0:
        return "Errors:\n" + "\n".join([f"{"NEW ERROR " if error.is_new_this_run else ""}{error.company_name}{f" ({error.company_name}, {error.jobs_page})" if {error.company_name} else ""}: {error.message}" for error in errors])
    return "No errors."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape new jobs.')
    parser.add_argument('config_scrapers_folder', type=str, help='Path to folder with config.py and scrapers.py')
    parser.add_argument('run_record_json', type=str, help='Path to file storing history of prior run(s)')
    parser.add_argument('--additional_search_term', type=str, default=None, help='Search term to add in considering a job relevant')
    parser.add_argument('--limit_company', type=str, default=None, help='Search only companies that contain this string in their name')
    parser.add_argument('--dont_replace_run_record', action='store_true', help="Don't replace the run record file")
    parser.add_argument('--dont_write_run_record', action='store_true', help="Don't write the run record file")
    parser.add_argument('--headless', action='store_true', help="Run headless")
    parser.add_argument('--default_sleep', type=int, default=1, help="Seconds to sleep on load and after scroll")
    args = parser.parse_args()

    sys.path.append(os.path.abspath(args.config_scrapers_folder))

    with open(args.run_record_json) as f:
        run_record = RunRecord.from_dict(json.load(f))

    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    if args.headless:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    new_relevant_jobs, run_record, verify_no_jobs, errors_message = get_new_relevant_jobs(
        driver, 
        run_record,
        args.limit_company,
        args.additional_search_term,
        args.default_sleep
    )

    if len(verify_no_jobs) > 0:
        print(bcolors.OKBLUE + "No jobs at all, but no specific no jobs phrase:\n" + "\n".join([company.name for company in verify_no_jobs]) + bcolors.ENDC)
    if len(new_relevant_jobs) > 0:
        print(bcolors.OKGREEN + format_new_jobs_message(new_relevant_jobs) + bcolors.ENDC)
    if len(run_record.errors) > 0:
        print(bcolors.FAIL + errors_message + bcolors.ENDC)
    if len(new_relevant_jobs) == 0:
        print("No new jobs")

    if len(new_relevant_jobs) > 0 and not args.dont_write_run_record: # disconnected logic not tied with a hard constraint
        filename = args.run_record_json
        if args.dont_replace_run_record:
            path, extension = os.path.splitext(filename)
            filename = f"{path}_{str(datetime.datetime.now()).replace(" ", "_")}{extension}"
        with open(filename, 'w') as f:
            json.dump(asdict(run_record), f, indent=4)
        print(f"Wrote new existing jobs to {filename}")
