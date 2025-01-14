# Usage

## Programming 102/tips on writing scrapers

For said non-software-engineer friends

Anatomy of a scraper
```py
class WriteYourOwnPage:
    @staticmethod
    def get_jobs(driver):
        # optional: find a container, with an id, that has all the job postings
        container = driver.find_element(By.ID, 'jobs')
        # find job elements (within the container element)
        job_elements = container.find_elements(By.CLASS_NAME, "job-posting")
        
        # keep these next two lines
        jobs = [] # create an empty list for jobs that we will collect
        for job in job_elements: # loop through the job_elements we have found

            # job.find_element(By.TAG_NAME, "a"): within the job element, get the <a> link element
            # .get_attribute("href"): within that element, get the value of the href attribute (i.e., the link)
            link_url = job.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            jobs.append(
                JobPosting(
                    title=job.text, # grab all the text inside the job element
                    id=link_url, # the link_url we found above will be the id
                    link=link_url, # this is optional. if you can find an id but not a link, feel free to omit this line
                )
            )
        return jobs
```

Add `breakpoint()` in a scraper to pause there and poke around. E.g., 
```py
job_elements = driver.find_element(By.TAG_NAME, 'main').find_elements(By.TAG_NAME, "li")
breakpoint()

# Run the script
# When it pauses, I can type `job_elements` to check its value. E.g., am I even retrieving anything?
job_elements
# Might output something like
[]
# Meaning that it didn't get anything!
```

A `JobPosting` requires a `title` and `id`.
```py
JobPosting(
    title=job.text, # Doesn't only need to be the title. Can be all the text you want to include in the email or search for relevance in. If it's easier to grab more excess text, just grab more excess text.
    id=link_url, # Should uniquely identify a posting within a given company. A job is only considered "new" if it has a different ID from any other ID seen for this company before.
    link=link_url, # This line is optional. If it's hard to get, you can just delete this line. If provided it will be included in the email. If not, when you get the email you can manually check the company careers page.
)
```

```sh
# Sound notification when done
python3 job_scrape.py configs/ data/run_record.json && say "done"

# Temporarily include an additional search term to verify that the scraper was successfully able to grab jobs on the page (even if none currently are relevant)
python3 job_scrape.py configs/ data/run_record.json --add_search_term "director"

# Combine limiting to one company (that you are writing the scraper for) and including an additional temporary search term
python3 job_scrape.py configs/ data/run_record.json --limit_company "example company name" --add_search_term "director"

# Combine with not overwriting the existing jobs file, so that you can keep running the same command to test if the scraper works. There should be a new file with the timestamp in outputs/ that includes the found new director job
python3 job_scrape.py configs/ data/run_record.json --limit_company "example company name" --add_search_term "director" --dont_replace_run_record
```

Selenium documentation:
https://www.selenium.dev/documentation/webdriver/elements/locators/

`.find_element(...)` will error if no element is found.
`.find_elements(...)` (note the plural) will happily keep going if no element(s) are found. If you have a loop through the elements after, it will just not loop through anything.

If you get an error message, search it up.


## Privacy

I'm not going to deliberately look through your list of companies, but as the hosting account owner I cannot remove myself from having permissions to access your uploaded files.

Additionally, I will sometimes look at logs in order to debug errors. Anything you `print()`, or potentially errors in your code, will end up in logs that I may see while looking at logs to fix errors. Thus, I may as a side effect see the companies, etc that you are scraping. These logs are deleted after 1 month.

I won't act on anything I see, including that I will not use or share any information I see for my own job search or anyone else's.

This is about the level of privacy you would expect with the employees of any website you use, but in this case you personally know the only employee.
