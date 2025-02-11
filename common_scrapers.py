import requests
import json
from models import *
from selenium.webdriver.common.by import By

class GreenhousePage:
    @staticmethod
    def get_jobs(driver, config=None):
        job_elements = driver.find_elements(By.CLASS_NAME, 'job-post')
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs

class GreenhouseEmbeddedStandalonePage:
    @staticmethod
    def get_jobs(driver, config=None):
        job_elements = driver.find_elements(By.CLASS_NAME, 'opening')
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs

class GreenhouseEmbeddedPage:
    @staticmethod
    def get_jobs(driver, config=None):
        time.sleep(2)
        greenhouse_iframe = driver.find_element(By.ID, "grnhse_iframe")
        assert greenhouse_iframe.tag_name == "iframe"
        driver.switch_to.frame(greenhouse_iframe)
        return GreenhouseEmbeddedStandalonePage.get_jobs(driver)

class LeverCoPage:
    @staticmethod
    def get_jobs(driver, config=None):
        job_elements = driver.find_elements(By.CLASS_NAME, 'posting')
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs

class BambooPage:
    @staticmethod
    def get_jobs(driver, config=None):
        job_elements = driver.find_element(By.TAG_NAME, 'main').find_elements(By.TAG_NAME, "li")
        jobs = []
        for job in job_elements:
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=job.find_element(By.TAG_NAME, 'a').get_attribute("href"),
                )
            )
        return jobs

class WorkablePage:
    @staticmethod
    def get_jobs(driver, config=None):
        container = driver.find_element(By.ID, "jobs")
        job_elements = container.find_elements(By.XPATH, '//li[@data-ui="job"]')
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                )
            )
        return jobs

class WorkdayPage:
    @staticmethod
    def get_jobs(driver, config=None):
        time.sleep(1)

        PAUSE_TIME = 2
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to bottom
        time.sleep(PAUSE_TIME)

        click_counter = 0
        while len(driver.find_elements(By.XPATH, '//button[@data-uxi-widget-type="stepToNextButton"]')) > 0 and driver.find_element(By.XPATH, '//button[@data-uxi-widget-type="stepToNextButton"]').is_displayed():
            driver.find_element(By.XPATH, '//button[@data-uxi-widget-type="stepToNextButton"]').click()
            time.sleep(PAUSE_TIME)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll to bottom
            time.sleep(PAUSE_TIME)
            click_counter += 1
        
        print("Workday clicked next", click_counter, "times")

        logs = driver.get_log("performance")
        relevant_logs = [json.loads(log["message"]) for log in logs if "Network.responseReceived" in log["message"]]
        request_ids = [log['message']['params']['requestId'] for log in relevant_logs if 'response' in log['message']['params'] and 'url' in log['message']['params']['response'] and "/jobs" in log['message']['params']['response']['url'] and log['message']['params']['type'] == 'Fetch']
        assert len(request_ids) >= 1

        nested_job_postings = [json.loads(driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})['body'])['jobPostings'] for request_id in request_ids]
        print("Got workday data with", len(request_ids), "requests")

        jobs = []
        for job_postings in nested_job_postings:
            for job in job_postings:
                if 'title' in job: # there are inconsistently sometimes entries that have no title or externalPath, just the bulletFields field
                    link_url = driver.current_url.split("?")[0] + job['externalPath']
                    jobs.append(
                        JobPosting(
                            title=job['title'],
                            id=link_url,
                            link=link_url,
                        )
                    )
        return jobs

class RipplingPage:
    @staticmethod
    def get_jobs(driver, config=None):
        all_anchors = driver.find_elements(By.TAG_NAME, 'a')
        job_elements = [el.find_element(By.XPATH, './../..') for el in all_anchors if 'jobs' in el.get_attribute("href") and el.text != "Apply"]
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text + " (note this only shows one location but there might be multiple for this same link)",
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs

class AshbyPage:
    @staticmethod
    def get_jobs(driver, config=None):
        root = driver.find_element(By.ID, 'root')
        containers = root.find_elements(By.CLASS_NAME, 'ashby-job-posting-brief-list')
        jobs = []
        for container in containers:
            job_elements = container.find_elements(By.TAG_NAME, 'a')
            for job in job_elements:
                link_url = job.get_attribute("href")
                jobs.append(
                    JobPosting(
                        title=job.text,
                        id=link_url,
                        link=link_url,
                    )
                )
        return jobs

class AshbyEmbeddedPage:
    @staticmethod
    def get_jobs(driver, config=None):
        ashby_iframe = driver.find_element(By.ID, "ashby_embed_iframe")
        assert ashby_iframe.tag_name == "iframe"
        driver.switch_to.frame(ashby_iframe)

        return AshbyPage.get_jobs(driver)


class ApplyToJobPage:
    @staticmethod
    def get_jobs(driver, config=None):
        container = driver.find_element(By.CLASS_NAME, 'jobs-list')
        job_elements = container.find_elements(By.CSS_SELECTOR, 'li.list-group-item')
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs

class SmartRecruitersPage:
    @staticmethod
    def get_jobs(driver, config=None):
        container = driver.find_element(By.CLASS_NAME, 'openings-body')
        job_elements = container.find_elements(By.CSS_SELECTOR, 'li.opening-job')
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, 'a').get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs


"""
Only gets jobs from the last 10 days

All config keys optional
"config": {
    "exclude_search_terms": [ "intern", "QA"],
    "excluded_companies": ["tesla"],
    "countries": ["Remote", "Multiple Locations", "Anywhere", "United States"],
    "local_locations": ["NY", "NYC"],
    "only_include_local_or_remote": true
}

exclude_search_terms: If specified, will not include if title contains any of these terms
excluded_companies: If specified, will not include if company
countries: If specified, will only include if the Country column contains any of these terms, or is empty. Locations are CASE SENTITIVE.
local_locations: If specified, will label with a 🏠 emoji. Locations are CASE SENTITIVE.
only_include_local_or_remote: If true, will only include if location is in local_locations, or remote allowed
"""
class ClimateTechListPage(JobsPage):
    @staticmethod
    def get_jobs(driver, config=None):
        logs = driver.get_log("performance")
        networks = []

        data = None
        for log in logs:
            message = log["message"]
            if "readSharedViewData" in message:
                message_dict = json.loads(log["message"])
                if message_dict["message"]["method"] == "Network.requestWillBeSent":
                    driver.execute_script("window.stop();")
                    request_info = message_dict["message"]["params"]["request"]
                    data = requests.get(request_info["url"], headers = request_info["headers"]).json()
                    print("got data")

        columns = data["data"]["table"]["columns"]
        # order determines title composition
        relevant_column_names = [
            "Position Title",
            "Company",
            "Country",
            "Job Location",
            "Date first listed",
            "Remote",
            # "Company Vertical", values are dict {'valuesByForeignRowId': {'rec505JOieCJNncoi': ['selCodWauUmGOavwy']}, 'foreignRowIdOrder': ['rec505JOieCJNncoi']}
            # "Org Type", values are dict {'valuesByForeignRowId': {'rec505JOieCJNncoi': 'For-profit'}, 'foreignRowIdOrder': ['rec505JOieCJNncoi']}
        ]

        column_order_for_other_locations = ["Job Location"] + [x for x in relevant_column_names if x != "Job Location"]

        relevant_column_ids = {name: next(col["id"] for col in columns if col["name"].lower() == name.lower()) for name in relevant_column_names}

        country_choices = next(col["typeOptions"]["choices"] for col in columns if col["name"] == "Country")
        id_to_country = {key: value["name"] for key, value in country_choices.items()}

        rows = data["data"]["table"]["rows"]

        today = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(days = 10)
        time_cutoff = today - delta

        def has_relevant_title(row):
            if "exclude_search_terms" in config:
                lower_title = row["cellValuesByColumnId"][relevant_column_ids["Position Title"]].lower()
                if any(term in lower_title for term in set(config["exclude_search_terms"])):
                    return False

            return True

        def has_relevant_location(row):
            # Assumes capitalization
            location = row["cellValuesByColumnId"][relevant_column_ids["Job Location"]]

            if "excluded_locations" in config and any(term in location for term in set(config["excluded_locations"])):
                return False
            
            if location.strip() == "":
                return True

            if "local_locations" in config and any(term in location for term in set(config["local_locations"])):
                return True
                
            if "countries" in config:
                if relevant_column_ids["Country"] not in row["cellValuesByColumnId"]:
                    # no Country data
                    return True
                if not len(row["cellValuesByColumnId"][relevant_column_ids["Country"]]) > 0:
                    print(row["cellValuesByColumnId"][relevant_column_ids["Country"]])
                if len({id_to_country[country] for country in row["cellValuesByColumnId"][relevant_column_ids["Country"]]}.intersection(set(config["countries"]))) > 0:
                    return True
                else:
                    return False

            return True

        def should_exclude_company(row):
            if "excluded_companies" in config:
                return row["cellValuesByColumnId"][relevant_column_ids["Company"]] in set(config["excluded_companies"])

        def is_relevant(row):
            was_created_recently = datetime.datetime.fromisoformat(row["createdTime"]) >= time_cutoff

            # dynamically calls
            return was_created_recently and has_relevant_location(row) and has_relevant_title(row) and not should_exclude_company(row)

        def format_title(row, column_names):
            cols = []
            for name in column_names:
                if name == "Country" and relevant_column_ids["Country"] in row["cellValuesByColumnId"]:
                    cols.append(", ".join([id_to_country[country_id] for country_id in row["cellValuesByColumnId"][relevant_column_ids["Country"]]]))
                else:
                    cols.append(row["cellValuesByColumnId"].get(relevant_column_ids[name], ""))
            return ". ".join(cols)

        local_jobs = []
        remote_jobs = []
        _other_jobs = []
        for row in rows:
            # time created in climatetechlist, not posting time
            if is_relevant(row):
                job = JobPosting(
                    title=None,
                    id=row["id"]
                )
                if "local_locations" in config and any(term in row["cellValuesByColumnId"][relevant_column_ids["Job Location"]] for term in set(config["local_locations"])):
                    title = format_title(row, relevant_column_names)
                    job.title = f"🏠 {title}"
                    local_jobs.append(job)
                elif "Remote" in row["cellValuesByColumnId"][relevant_column_ids["Remote"]]:
                    title = format_title(row, relevant_column_names)
                    job.title = f"💻 {title}"
                    remote_jobs.append(job)
                else:
                    # put job location first
                    title = format_title(row, column_order_for_other_locations)
                    job.title = title
                    _other_jobs.append(job)

        # ignore other jobs
        if "only_include_local_or_remote" in config and config["only_include_local_or_remote"]:
            return local_jobs + remote_jobs    
        else:
            return local_jobs + remote_jobs + _other_jobs

