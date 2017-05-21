import os

import scrapy
import youtube_dl


class StartASLSpider(scrapy.Spider):
    """Crawl the Free ASL 1, 2, & 3 Classes at StartASL.com For Videos."""

    name = "StartASL"
    start_urls = ['https://www.startasl.com/learn-sign-language-asl.html']
    video_name_template = '%(title)s.%(ext)s'


    def parse(self, response):
        """Parse the Contents Page & Dispatch Requests For Each Unit."""
        table_rows = response.css('.entry-content table tr')

        # Remove the Header & Fingerspelling Rows
        table_rows = table_rows[1:-1]

        # Split the Class & Units
        table_rows = [
            (row.css('td')[0].css('::text').extract_first().replace(' ', '_'),
             row.css('td a')) for row in table_rows
        ]

        # Ensure Directories For Each Class Exists
        os.makedirs(os.path.join(os.curdir, 'output'), exist_ok=True)
        for (class_name, _) in table_rows:
            folder_name = '{}'.format(class_name.replace(' ', '_'))
            os.makedirs(
                os.path.join(os.curdir, 'output', folder_name), exist_ok=True
            )

        # Parse the Unit Pages
        for (class_name, unit_links) in table_rows:
            for link in unit_links:
                unit_name = link.css('::text').extract_first().replace(' ', '_')
                unit_url = link.css('::attr(href)').extract_first()
                response = scrapy.Request(unit_url, callback=self.parse_unit)
                response.meta['class_name'] = class_name
                response.meta['unit_name'] = unit_name
                yield response


    def parse_unit(self, response):
        """Parse a Class' Unit Page & Download any Phrase or Vocab Videos."""
        class_name = response.meta['class_name']
        unit_name = response.meta['unit_name']

        self.logger.info("Parsing {} - {}".format(class_name, unit_name))

        is_pdf = response.url.split(os.extsep)[-1].lower() == 'pdf'

        if is_pdf:
            # Save the PDF
            pdf_path = os.path.join(
                os.curdir, 'output', class_name,
                '{}{}{}'.format(unit_name, os.extsep, 'pdf')
            )
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.body)
        else:
            # Parse the Video Lists
            video_lists = response.css('.dictionary.phrase-list')

            # Skip Units with No Video Lists
            if not video_lists:
                return

            self.logger.info("Downloading Videos For {} - {}".format(
                class_name, unit_name))

            # Ensure a Directory for the Unit Exists
            os.makedirs(
                os.path.join(os.curdir, 'output', class_name, unit_name),
                exist_ok=True)

            # Determine Which Video Lists Exist Exists
            if len(video_lists) == 1:
                if '1' in class_name:
                    # Some ASL1 Units Don't Have Phrases
                    phrase_list = None
                    vocab_list = video_lists[0]
                else:
                    # The Free ASL2 & ASL3 Units Don't Have Vocab Videos
                    phrase_list = video_lists[0]
                    vocab_list = None
            else:
                phrase_list = video_lists[0]
                vocab_list = video_lists[1]

            # Download the Phrase Videos
            if phrase_list is not None:
                phrase_video_urls = phrase_list.css('.phrase a::attr(current-url)').extract()
                if phrase_video_urls:
                    phrase_dir = os.path.join(
                        os.curdir, 'output', class_name, unit_name, 'phrases')
                    os.makedirs(phrase_dir, exist_ok=True)
                    phrase_yt_options = {
                        'outtmpl': os.path.join(phrase_dir, self.video_name_template),
                        'quiet': True,
                    }
                    with youtube_dl.YoutubeDL(phrase_yt_options) as ydl:
                        ydl.download(phrase_video_urls)


            # Download the Vocab Videos
            if vocab_list is not None:
                vocab_video_urls = vocab_list.css('.phrase a::attr(current-url)').extract()
                if vocab_video_urls:
                    vocab_dir = os.path.join(
                        os.curdir, 'output', class_name, unit_name, 'vocab')
                    os.makedirs(vocab_dir, exist_ok=True)
                    vocab_yt_options = {
                        'outtmpl': os.path.join(vocab_dir, self.video_name_template),
                        'quiet': True,
                    }
                    with youtube_dl.YoutubeDL(vocab_yt_options) as ydl:
                        ydl.download(vocab_video_urls)
