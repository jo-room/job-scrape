#! /usr/bin/env python3
# Need selenium because postings might take js to load

import argparse
import datetime
import traceback
import json
import os
import sys
import shutil
import importlib
import time
from collections import defaultdict
from dataclasses import asdict
from tempfile import mkdtemp

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

from models import *

# Common entrypoint
def get_new_relevant_jobs(driver, run_record: RunRecord, companies, search_terms, limit_company = None, add_search_term = None, default_sleep = 1):

    existing_jobs = defaultdict(set, {key: set(value) for key, value in run_record.existing_jobs.items()})

    relevant_jobs, skipped_companies, verify_no_jobs, errors = get_relevant_jobs(driver, limit_company, add_search_term, default_sleep, companies, search_terms) 

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

def get_relevant_jobs(driver, limit_company, add_search_term, default_sleep, companies, search_terms):
    relevant_jobs: list[tuple[Company, JobPosting]] = []
    skipped_companies = []
    verify_no_jobs = []
    errors: list[tuple[Company, Exception]] = []

    if add_search_term:
        search_terms.append(add_search_term)

    for company in companies:
        if limit_company and limit_company.lower() not in company.name.lower():
            continue

        if company.active:
            print("Checking", company.name)
            try:
                if company.is_crunchbase:
                    company_relevant_jobs, jobs_page_status = get_crunchbase_companies(driver, company, default_sleep)
                else:
                    assert company.jobs_page
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

def get_crunchbase_companies(driver, company, default_sleep) -> (list[JobPosting], JobsPageStatus):
    jobs_page_status = JobsPageStatus.NO_JOBS_PHRASE_NOT_FOUND_BUT_NO_JOBS
    jobs = []
    job_ids = set()
    for page_type, scrape_page in company.scrape_pages:
        driver.get(scrape_page)
        time.sleep(company.load_sleep if company.load_sleep else default_sleep)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to bottom to lazy load everything
        time.sleep(company.scroll_sleep if company.scroll_sleep else default_sleep)

        page_jobs = company.jobs_page_class[page_type].get_jobs(driver)
        
        if len(page_jobs) > 0:
            jobs_page_status = JobsPageStatus.SOME_JOB_FOUND

        for job in page_jobs:
            job.title = job.title + f" ({scrape_page})"
            if job.id not in job_ids:
                job_ids.add(job.id)
                jobs.append(job)

    jobs.sort(key=lambda x: (x.date is not None, x.date), reverse=True)
    return jobs, jobs_page_status


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
            jobs = company.jobs_page_class.get_jobs(driver, company.config)
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
    terms_to_use = search_terms
    if company.relevant_search_terms:
        terms_to_use = company.relevant_search_terms

    if len(terms_to_use) == 0:
        return True

    return any(search_term.lower() in title.lower() for search_term in terms_to_use)

def format_new_jobs_message(new_jobs: dict[str, dict[str, any]]) -> str:
    message = ""
    for company_name, info in new_jobs.items():
        message += f"\n{company_name} ( {info["company"].jobs_page} ):\n"
        for job in info["jobs"]:
                message += f"\t {job.title.replace("\n", " ")} {job.link if job.link else ""}\n"
    return message

def format_errors_message(errors: list[ScrapeError]) -> str:
    if len(errors) > 0:
        return "Errors:\n" + "\n".join([f"{"NEW ERROR " if error.is_new_this_run else ""}{error.company_name}{f" ({error.company_name}, {error.jobs_page})" if {error.company_name} else ""}: {error.message}" for error in errors])
    return "No errors."


# From https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def get_companies(config_companies, additional_scrapers_module=None):
    import common_scrapers
    import inspect
    all_scrapers = {}
    for name, obj in inspect.getmembers(common_scrapers):
        if inspect.isclass(obj):
            all_scrapers[name] = obj
    if additional_scrapers_module:
        for name, obj in inspect.getmembers(additional_scrapers_module):
            if inspect.isclass(obj):
                all_scrapers[name] = obj

    companies = []
    for company in config_companies:
        company["jobs_page_class"] = all_scrapers[company["jobs_page_class_name"]]
        companies.append(Company(**company))
    return companies
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape new jobs.')
    parser.add_argument('config_file', type=str, help='Path to config.json or config.py file')
    parser.add_argument('run_record_json', type=str, help='Path to file storing history of prior run(s)')
    parser.add_argument('--add_scrapers_file', type=str, default=None, help='Path to file with additional scrapers')
    parser.add_argument('--limit_company', type=str, default=None, help='Search only companies that contain this string in their name')
    parser.add_argument('--add_search_term', type=str, default=None, help='Search term to add in considering a job relevant')
    parser.add_argument('--dont_write_run_record', action='store_true', help="Don't write the run record file")
    parser.add_argument('--dont_replace_run_record', action='store_true', help="Don't replace the run record file")
    parser.add_argument('--backup_run_record', action='store_true', help="Rename the original run record file to <original file name>_backup.json")
    parser.add_argument('--headless', action='store_true', help="Run headless")
    parser.add_argument('--default_sleep', type=int, default=1, help="Seconds to sleep on load and after scroll")
    args = parser.parse_args()

    with open(args.run_record_json) as f:
        run_record = RunRecord.from_dict(json.load(f))

    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    if args.headless:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    if args.add_scrapers_file:
        additional_scrapers_module = import_from_path("scrapers", args.add_scrapers_file)
    else:
        additional_scrapers_module = None

    if args.config_file.endswith(".json"):
        with open(args.config_file) as f:
            config = json.load(f)
            companies = get_companies(config["companies"], additional_scrapers_module)
            search_terms = config["search_terms"]
    else:
        config_module = import_from_path("config", args.config_file)
        companies = [Company(**company) for company in config_module.get_companies(additional_scrapers_module)]
        search_terms = config_module.search_terms

    new_relevant_jobs, run_record, verify_no_jobs, errors_message = get_new_relevant_jobs(
        driver, 
        run_record,
        companies,
        search_terms,
        args.limit_company,
        args.add_search_term,
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

    if len(new_relevant_jobs) > 0:
        filename = args.run_record_json

        if args.backup_run_record:
            path, extension = os.path.splitext(filename)
            backup_dest = f"{path}_backup{extension}"
            shutil.copy2(filename, backup_dest)
            print(f"Backed up {filename} to {backup_dest}")

        if not args.dont_write_run_record:
            if args.dont_replace_run_record:
                path, extension = os.path.splitext(filename)
                filename = f"{path}_{str(datetime.datetime.now()).replace(" ", "_")}{extension}"
            with open(filename, 'w') as f:
                json.dump(asdict(run_record), f, indent=4)
            print(f"Wrote new existing jobs to {filename}")
