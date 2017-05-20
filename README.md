# Start ASL Course Video Downloader

This is a Python 3 Script that uses Scrapy & Youtube-DL to download the Phrase
& Vocabulary videos from the Free American Sign Language 1, 2, & 3 Courses at
http://startasl.com.

Unit descriptions and inline videos may be added at a later point.

You need Python3 & pip to run this script:

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
scrapy runspider scrape.py
```


## License

GPLv3
