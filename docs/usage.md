# Usage

For said non-software-engineer friends

## Installation
Download and install
- PyCharm Community Edition (might need to scroll down for the Community Edition): https://www.jetbrains.com/pycharm/download/


## Programming 102/tips on writing scrapers

### Running
```sh
# Sound notification when done
python3 job_scrape.py configs/config.json data/run_record.json && say "done"

# List all flags
python3 job_scrape.py --help

# Temporarily include an additional search term to verify that the scraper was successfully able to grab jobs on the page (even if none currently are relevant)
python3 job_scrape.py configs/config.json data/run_record.json --add_search_term "director"

# Combine limiting to one company (that you are writing the scraper for) and including an additional temporary search term
python3 job_scrape.py configs/config.json data/run_record.json --limit_company "example company name" --add_search_term "director"

# Combine with not overwriting the existing jobs file, so that you can keep running the same command to test if the scraper works. There should be a new file with the timestamp in outputs/ that includes the found new director job
python3 job_scrape.py configs/config.json data/run_record.json --limit_company "example company name" --add_search_term "director" --dont_replace_run_record
```

### Debugging tips

`print()` and `breakpoint()`

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

### Filling out the field for a JobPosting

A `JobPosting` requires a `title` and `id`.
```py
JobPosting(
    title=job.text, # Doesn't only need to be the title. Can be all the text you want to include in the email or search for relevance in. If it's easier to grab more excess text, just grab more excess text.
    id=link_url, # Should uniquely identify a posting within a given company. A job is only considered "new" if it has a different ID from any other ID seen for this company before.
    link=link_url, # This line is optional. If it's hard to get, you can just delete this line. If provided it will be included in the email. If not, when you get the email you can manually check the company careers page.
)
```

### Finding HTML elements on a page
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

If you want to run things without me having access to them, you can run the scrape locally on your computer.
