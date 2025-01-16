import json
from models import *
from selenium.webdriver.common.by import By

class BitsInBioPage:
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

# Ask me for the climatetechlist scraper

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