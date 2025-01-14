from models import *

search_terms = ["software", "developer", "engineer", "frontend", "front end", "front-end", "backend", "back end", "back-end", "fullstack", "full stack", "full-stack", "various roles"]

def get_companies(scrapers):
	return [
		{
			"name": "Crunchbase Companies",
			"is_crunchbase": True,
			"scrape_pages": [
				(CrunchbasePageType.HUB, "https://www.crunchbase.com/hub/<url here>"),
				(CrunchbasePageType.DISCOVER, "https://www.crunchbase.com/discover/saved/<url here>"),
				(CrunchbasePageType.DISCOVER, "https://www.crunchbase.com/lists/<url here>"),
			],
			"jobs_page_class": {
				CrunchbasePageType.HUB: scrapers.CrunchbaseHubPage,
				CrunchbasePageType.DISCOVER: scrapers.CrunchbaseDiscoverPage
			},
		}
	]