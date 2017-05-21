import os

import scrapy
import youtube_dl


class StartASLSpider(scrapy.Spider):
    """Crawl the Free ASL 1, 2, & 3 Classes at StartASL.com For Videos."""

    name = "StartASL"
    start_urls = ['https://www.startasl.com/learn-sign-language-asl.html']
    video_name_template = '%(title)s.%(ext)s'
    output_directory_name = 'output'
    disable_youtubedl_output = True


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
        self._make_output_directory()
        for (class_name, _) in table_rows:
            self._make_output_directory(class_name)

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

        if not self._save_if_pdf(class_name, unit_name, response):
            # Parse the Video Lists
            video_lists = response.css('.dictionary.phrase-list')

            # Skip Units with No Video Lists
            if not video_lists:
                return

            self.logger.info("Downloading Videos For {} - {}".format(
                class_name, unit_name))

            # Ensure a Directory for the Unit Exists
            self._make_output_directory(class_name, unit_name)

            # Determine Which Video Lists Exist
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

            self._download_videos_from_list(
                class_name, unit_name, 'phrases', phrase_list)
            self._download_videos_from_list(
                class_name, unit_name, 'vocab', vocab_list)


    @classmethod
    def _make_output_directory(cls, *args):
        path = os.path.join(os.curdir, cls.output_directory_name, *args)
        os.makedirs(path, exist_ok=True)
        return path


    @classmethod
    def _save_if_pdf(cls, class_name, unit_name, response):
        if response.url.split(os.extsep)[-1].lower() == 'pdf':
            pdf_path = os.path.join(
                os.curdir, cls.output_directory_name, class_name,
                '{}{}{}'.format(unit_name, os.extsep, 'pdf')
            )
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.body)
                self.logger.info('Downloaded PDF for {} - {}'.format(
                    class_name, unit_name))
            return True
        else:
            return False


    @classmethod
    def _download_videos_from_list(cls, class_name, unit_name, video_type, video_list):
        if video_list is not None:
            urls = video_list.css('.phrase a::attr(current-url)').extract()
            if urls:
                video_dir = cls._make_output_directory(
                    class_name, unit_name, video_type)
                youtubedl_options = {
                    'outtmpl' : os.path.join(video_dir, cls.video_name_template),
                    'quiet': cls.disable_youtubedl_output,
                }
                with youtube_dl.YoutubeDL(youtubedl_options) as downloader:
                    downloader.download(urls)
