# Start ASL Free Course Downloader

This is a Python 3 Script that uses Scrapy & Youtube-DL to download the the
Free American Sign Language 1, 2, & 3 Courses at http://startasl.com.

The contents for each Class and Unit are saved into separate
folders(`ASL_1/Unit_1/`, `ASL_2/Workbook.pdf`, etc.). Each Unit's text is saved
as a Markdown file(`lesson.md`) and the videos are sorted into `lesson`,
`phrases`, & `vocab` folders. The filenames for the `lesson` & `phrases` videos
are prefixed with a number so that you can play them in the same order as the
website(the `vocab` videos on the website are always in alphabetical order).


You need Python 3 to run this script:

```
# Grab the Code
git clone http://github.com/prikhi/Start-ASL-Downloader startASL
cd startASL

# Setup & Activate a Virtual Environment
python -m venv Env
source Env/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Run the Scraper
scrapy runspider scrape.py -L INFO
```


## License

GPLv3
