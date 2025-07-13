import json
from models import *
from selenium.webdriver.common.by import By


class WriteYourOwnPage:
    @staticmethod
    def get_jobs(driver):
        container = driver.find_element(By.ID, "jobs")
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
