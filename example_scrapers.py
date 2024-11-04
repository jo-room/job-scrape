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

class GreenhouseEmbeddedPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
        greenhouse_iframe = driver.find_element(By.ID, "grnhse_iframe")
        assert greenhouse_iframe.tag_name == "iframe"
        driver.switch_to.frame(greenhouse_iframe)
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
        job_elements = driver.find_elements(By.XPATH, '//li[@data-ui="job-opening"]')
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