import json
import requests
import datetime

from selenium.webdriver.common.by import By
from models import *

EXCLUDED_COMPANIES = {}


class CrunchbaseDiscoverPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
        time.sleep(3)
        container = driver.find_element(By.TAG_NAME, "results").find_element(
            By.TAG_NAME, "grid-body"
        )
        job_elements = container.find_elements(By.TAG_NAME, "grid-row")

        jobs = []
        for job in job_elements:
            date_text = job.find_element(
                By.XPATH, './grid-cell[@data-columnid="announced_on"]'
            ).text
            date = datetime.datetime.strptime(date_text, "%b %d, %Y")

            transaction_name_el = job.find_element(
                By.XPATH, './grid-cell[@data-columnid="identifier"]'
            )
            link_el = transaction_name_el.find_element(By.TAG_NAME, "a")
            link_url = link_el.get_attribute("href")
            if not any(
                company_name in link_el.text for company_name in EXCLUDED_COMPANIES
            ):
                jobs.append(
                    JobPosting(
                        title=f"{date_text} {link_el.text}",
                        id=link_url,
                        link=link_url,
                        date=date,
                    )
                )
        return jobs


class CrunchbaseHubPage(JobsPage):
    @staticmethod
    def get_jobs(driver):
        return (
            get_funding_companies(driver)
            + get_leaderboard_companies(driver)
            + get_recent_activities_funding_rounds_companies(driver)
            + get_people_companies(driver)
        )


def get_leaderboard_companies(driver) -> list[JobPosting]:
    section = driver.find_element(By.XPATH, "//h2[text()='Leaderboard']").find_element(
        By.XPATH, "./../../../.."
    )
    assert section.tag_name == "mat-card"
    container = section.find_element(By.TAG_NAME, "list-card").find_element(
        By.TAG_NAME, "tbody"
    )
    job_elements = container.find_elements(By.TAG_NAME, "tr")

    jobs = []
    for job in job_elements:
        link_el = [
            el
            for el in job.find_elements(By.TAG_NAME, "a")
            if len(el.find_elements(By.CLASS_NAME, "identifier-image-and-label")) > 0
        ][0]
        link_url = link_el.get_attribute("href")

        if not any(company_name in link_el.text for company_name in EXCLUDED_COMPANIES):
            jobs.append(JobPosting(title=link_el.text, id=link_url, link=link_url))
    return jobs


def get_recent_activities_funding_rounds_companies(driver) -> list[JobPosting]:
    section = driver.find_element(
        By.XPATH, "//h2[text()='Recent Activities']"
    ).find_element(By.XPATH, "./../../../..")
    assert section.tag_name == "mat-card"
    container = section.find_element(By.TAG_NAME, "list-card").find_element(
        By.TAG_NAME, "tbody"
    )
    job_elements = container.find_elements(By.TAG_NAME, "tr")

    jobs = []
    for job in job_elements:
        date_text = job.find_element(By.CLASS_NAME, "field-type-date").text
        date = datetime.datetime.strptime(date_text, "%b %d, %Y")

        transaction_name_col_index = 2
        transaction_name_el = job.find_elements(By.TAG_NAME, "td")[
            transaction_name_col_index
        ]

        link_el = transaction_name_el.find_element(By.TAG_NAME, "a")
        link_url = link_el.get_attribute("href")
        if not any(company_name in link_el.text for company_name in EXCLUDED_COMPANIES):
            jobs.append(
                JobPosting(
                    title=f"{date_text} {link_el.text}",
                    id=link_url,
                    link=link_url,
                    date=date,
                )
            )
    return jobs


def get_funding_companies(driver) -> list[JobPosting]:
    section = driver.find_element(By.XPATH, "//h2[text()='Funding']").find_element(
        By.XPATH, "./../../../.."
    )
    assert section.tag_name == "mat-card"
    container = section.find_element(By.TAG_NAME, "list-card").find_element(
        By.TAG_NAME, "tbody"
    )
    job_elements = container.find_elements(By.TAG_NAME, "tr")
    jobs = []
    for job in job_elements:
        date_text = job.find_element(By.CLASS_NAME, "field-type-date").text
        date = datetime.datetime.strptime(date_text, "%b %d, %Y")

        link_el = [
            el
            for el in job.find_elements(By.TAG_NAME, "a")
            if "funding_round" in el.get_attribute("href")
        ][0]
        link_url = link_el.get_attribute("href")
        if not any(company_name in link_el.text for company_name in EXCLUDED_COMPANIES):
            jobs.append(
                JobPosting(
                    title=f"{date_text} {link_el.text}",
                    id=link_url,
                    link=link_url,
                    date=date,
                )
            )
    return jobs


def get_investments_companies(driver) -> list[JobPosting]:
    section = driver.find_element(By.XPATH, "//h2[text()='Investments']").find_element(
        By.XPATH, "./../../../.."
    )
    assert section.tag_name == "mat-card"
    container = section.find_element(By.TAG_NAME, "list-card").find_element(
        By.TAG_NAME, "tbody"
    )
    job_elements = container.find_elements(By.TAG_NAME, "tr")

    jobs = []
    for job in job_elements:
        date_text = job.find_element(By.CLASS_NAME, "field-type-date").text
        date = datetime.datetime.strptime(date_text, "%b %d, %Y")

        funding_round_col_index = 2
        funding_round_el = job.find_elements(By.TAG_NAME, "td")[funding_round_col_index]

        link_el = transaction_name_el.find_element(By.TAG_NAME, "a")
        link_url = link_el.get_attribute("href")
        if not any(company_name in link_el.text for company_name in EXCLUDED_COMPANIES):
            jobs.append(
                JobPosting(
                    title=f"{date_text} {link_el.text}",
                    id=link_url,
                    link=link_url,
                    date=date,
                )
            )
    return jobs


def get_people_companies(driver) -> list[JobPosting]:
    section = driver.find_element(By.XPATH, "//h2[text()='People']").find_element(
        By.XPATH, "./../../../.."
    )
    assert section.tag_name == "mat-card"
    container = section.find_element(By.TAG_NAME, "list-card").find_element(
        By.TAG_NAME, "tbody"
    )
    job_elements = container.find_elements(By.TAG_NAME, "tr")

    jobs = []
    for job in job_elements:
        company_col_index = 1
        company_el = job.find_elements(By.TAG_NAME, "td")[company_col_index]

        link_el = company_el.find_element(By.TAG_NAME, "a")
        link_url = link_el.get_attribute("href")
        jobs.append(JobPosting(title=link_el.text, id=link_url, link=link_url))
    return jobs
