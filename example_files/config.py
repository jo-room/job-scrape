from models import *

search_terms = ["software", "developer", "engineer", "frontend", "front end", "front-end", "backend", "back end", "back-end", "fullstack", "full stack", "full-stack"]

def get_companies(scrapers):
	return [
		{
			# Real example with minimum keys
			"name": "Bits in Bio",
			"jobs_page": "https://www.bitsinbio.org/jobs",
			"jobs_page_class": scrapers.BitsInBioPage,
		},
		{
			# Fake example demonstrating all keys. Keys match properties in class `Company`
			"name": "Example Company", # Required
			"jobs_page": "https://www.example.com/jobs", # Required for scraping
			"jobs_page_class": scrapers.LeverCoPage, # Required for scraping

			# Optional fine-tuning keys
			"active": False, # Temporarily turn this company off
			"no_jobs_phrase": "Sorry, we couldn't find anything here", # If specified, will search for of this phrase in the whole page to mean that there are no jobs. This is good to specify if you can. Make sure it's one continuous piece of text in the HTML, or use a shorter phrase that's continuous.
			"relevant_search_terms": ["carpenter", "rocket scientist"], # If specified, will only consider jobs with "carpenter" or "rocket scientist" relevant
			"load_sleep": 1, # Modify to increase/decrease the sleep time after load
			"scroll_sleep": 1, # Modify to increase/decrease the sleep time after scrolling to the bottom

			# Other optional keys for note taking, are not used
			"diff_page": False,
			"careers_landing_page": "", # E.g. An about page that leads to the careers listing page
			"location": "",
			"notes": "",
			"tags": [""],
			"what": "",
			"referral": "",
			"application_history": "",

		}
	]
