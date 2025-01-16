import json
from models import *
from selenium.webdriver.common.by import By

class JobsPage:
    @staticmethod
    def get_jobs(driver):
        raise NotImplementedError("Unexpected call to base class. Did you forget to specify \"jobs_page_class\" in config.py?")

class GreenhousePage(JobsPage):
    @staticmethod
    def get_jobs(driver): 
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

class GreenhouseEmbeddedStandalonePage(JobsPage):
    @staticmethod
    def get_jobs(driver):
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

class GreenhouseEmbeddedPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
        time.sleep(2)
        greenhouse_iframe = driver.find_element(By.ID, "grnhse_iframe")
        assert greenhouse_iframe.tag_name == "iframe"
        driver.switch_to.frame(greenhouse_iframe)
        return GreenhouseEmbeddedStandalonePage.get_jobs(driver)

class LeverCoPage(JobsPage):
    @staticmethod
    def get_jobs(driver): 
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

class BambooPage(JobsPage):
    @staticmethod
    def get_jobs(driver): 
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

class WorkablePage(JobsPage):
    @staticmethod
    def get_jobs(driver): 
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

class WorkdayPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
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
                link_url = driver.current_url.split("?")[0] + job['externalPath']
                jobs.append(
                    JobPosting(
                        title=job['title'],
                        id=link_url,
                        link=link_url,
                    )
                )
        return jobs

class RipplingPage(JobsPage):
    @staticmethod
    def get_jobs(driver): 
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

class AshbyPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
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

class AshbyEmbeddedPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
        ashby_iframe = driver.find_element(By.ID, "ashby_embed_iframe")
        assert ashby_iframe.tag_name == "iframe"
        driver.switch_to.frame(ashby_iframe)

        return AshbyPage.get_jobs(driver)


class ApplyToJobPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
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

class SmartRecruitersPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
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

class BitsInBioPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
        container = driver.find_element(By.ID, 'jobs')
        job_elements = container.find_elements(By.CLASS_NAME, 'MuiPaper-root')
        jobs = []
        for job in job_elements:
            links = [el for el in job.find_elements(By.TAG_NAME, "a")]
            link_el = next((el for el in links if el.get_attribute("textContent") == "Apply"), None)
            if not link_el:
                link_el = next((el for el in links if el.get_attribute("textContent") == "Contact"), None)
                assert link_el, "Error finding Apply or Contact"
            link_url = link_el.get_attribute("href")

            jobs.append(
                JobPosting(
                    title=job.find_element(By.CLASS_NAME, "MuiAccordionSummary-content").text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs

class WriteYourOwnPage:
    @staticmethod
    def get_jobs(driver):
        container = driver.find_element(By.ID, 'jobs')
        job_elements = container.find_elements(By.CLASS_NAME, "job-posting")
        
        jobs = []
        for job in job_elements:
            link_url = job.find_element(By.TAG_NAME, "a").get_attribute("href")
            jobs.append(
                JobPosting(
                    title=job.text,
                    id=link_url,
                    link=link_url,
                )
            )
        return jobs