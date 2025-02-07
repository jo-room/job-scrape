import time
import datetime

from typing import TypedDict
from dataclasses import dataclass
from enum import Enum

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CrunchbasePageType(Enum):
    HUB = 1
    DISCOVER = 2

@dataclass
class JobPosting:
    title: str
    id: str
    link: str = None
    date: datetime.date = None # only used for crunchbase

    def __post_init__(self):
        if self.title:
            assert isinstance(self.title, str), f"JobPosting title must be string, got type {type(self.title)} instead"
        assert isinstance(self.id, str) or isinstance(self.id, str) , f"JobPosting id must be int or string, got type {type(self.id)} instead"
        if self.link:
            assert isinstance(self.link, str), f"JobPosting link must be string, got type {type(self.link)} instead"

@dataclass
class Company:
    name: str
    active: bool = True
    careers_landing_page: str = None
    jobs_page: str = None
    jobs_page_class: any = None
    jobs_page_class_name: str = None
    load_sleep: int = None
    scroll_sleep: int = None
    diff_page: bool = False
    location: str = None
    no_jobs_phrase: str = None
    notes: str = None
    relevant_search_terms: list[str] = None
    tags: list[str] = None
    what: str = None
    referral: str = None
    application_history: str = None

    is_crunchbase: bool = False
    scrape_pages: [(str, CrunchbasePageType)] = None

class JobsPage:
    @staticmethod
    def get_jobs(driver):
        raise NotImplementedError("Unexpected call to base class")

class JobsPageStatus(Enum):
    SPECIFIC_NO_JOBS_PHRASE_FOUND = 1
    GENERIC_NO_JOBS_PHRASE_FOUND = 2
    NO_JOBS_PHRASE_NOT_FOUND_BUT_NO_JOBS = 3
    SOME_JOB_FOUND = 4
    NO_JOBS_FOUND = 5

@dataclass
class ScrapeError: # serializable
    company_name: str = None
    jobs_page: str = None
    message: str = None
    is_new_this_run: bool = False

@dataclass
class RunRecord:
    existing_jobs: dict[str, list[str]]
    errors: list[ScrapeError]

    @staticmethod
    def from_dict(run_record_dict):
        return RunRecord(
            existing_jobs=run_record_dict["existing_jobs"],
            errors=[ScrapeError(**error) for error in run_record_dict["errors"]]
        )
        
    def has_new_error(self) -> bool:
        return any(error.is_new_this_run for error in self.errors)
