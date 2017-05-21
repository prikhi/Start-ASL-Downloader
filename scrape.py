import io
import os

import html2text
import lxml.etree as etree
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
        class_names_and_unit_links = self._parse_class_table(response)

        self._make_output_directory()
        for (class_name, _) in class_names_and_unit_links:
            self._make_output_directory(class_name)

        # Parse the Unit Pages
        for (class_name, unit_links) in class_names_and_unit_links:
            for link in unit_links:
                yield from self._follow_unit_link(class_name, link)


    def parse_unit(self, response):
        """Parse a Class' Unit Page & Download any Phrase or Vocab Videos."""
        class_name = response.meta['class_name']
        unit_name = response.meta['unit_name']

        self.logger.info("Processing {} - {}".format(class_name, unit_name))

        if not self._save_if_pdf(class_name, unit_name, response):
            self._make_output_directory(class_name, unit_name)
            self._save_lesson_file(class_name, unit_name, response)
            self.logger.info("Downloading Lesson Videos")
            self._save_lesson_videos(class_name, unit_name, response)
            self.logger.info("Downloading Phrase & Vocabulary Videos")
            self._save_video_lists(class_name, unit_name, response)


    @classmethod
    def _parse_class_table(cls, response):
        table_rows = response.css('.entry-content table tr')
        table_rows = table_rows[1:-1]
        table_rows = [
            (row.css('td')[0].css('::text').extract_first().replace(' ', '_'),
             row.css('td a')) for row in table_rows
        ]
        return table_rows


    @classmethod
    def _make_output_directory(cls, *args):
        path = os.path.join(os.curdir, cls.output_directory_name, *args)
        os.makedirs(path, exist_ok=True)
        return path


    def _follow_unit_link(self, class_name, link):
        unit_name = link.css('::text').extract_first().replace(' ', '_')
        unit_url = link.css('::attr(href)').extract_first()
        response = scrapy.Request(unit_url, callback=self.parse_unit)
        response.meta['class_name'] = class_name
        response.meta['unit_name'] = unit_name
        yield response


    @classmethod
    def _save_if_pdf(cls, class_name, unit_name, response):
        if response.url.split(os.extsep)[-1].lower() == 'pdf':
            pdf_path = os.path.join(
                os.curdir, cls.output_directory_name, class_name,
                '{}{}{}'.format(unit_name, os.extsep, 'pdf')
            )
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.body)
            return True
        return False


    @classmethod
    def _save_lesson_file(cls, class_name, unit_name, response):
        lesson_html = response.css('.entry-content').extract_first()

        # Remove the Phrase & Vocab Lists
        html_parser = etree.HTMLParser(encoding='utf-8', recover=True)
        html_tree = etree.parse(io.StringIO(lesson_html), html_parser)
        for element in html_tree.xpath('//*[contains(@class,"phrase-list")]'):
            element.getparent().remove(element)

        # Convert the HTML Tree to Markdown
        lesson_markdown = html2text.html2text(
            etree.tostring(html_tree).decode('utf-8'))

        # Save the Unit Lesson Text
        lesson_path = os.path.join(os.curdir, cls.output_directory_name,
                                   class_name, unit_name, 'lesson.md')
        with open(lesson_path, 'w') as lesson_file:
            lesson_file.write(lesson_markdown)


    @classmethod
    def _save_lesson_videos(cls, class_name, unit_name, response):
        urls = response.css('video source::attr(src)').extract()
        cls._download_videos(class_name, unit_name, 'lesson', urls)


    @classmethod
    def _save_video_lists(cls, class_name, unit_name, response):
        video_lists = response.css('.dictionary.phrase-list')
        if video_lists:
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

            cls._download_videos_from_list(
                class_name, unit_name, 'phrases', phrase_list)
            cls._download_videos_from_list(
                class_name, unit_name, 'vocab', vocab_list, autonumber=False)


    @classmethod
    def _download_videos_from_list(cls, class_name, unit_name, video_type, video_list, autonumber=True):
        if video_list is not None:
            urls = video_list.css('.phrase a::attr(current-url)').extract()
            cls._download_videos(
                class_name, unit_name, video_type, urls, autonumber)


    @classmethod
    def _download_videos(cls, class_name, unit_name, video_type, urls, autonumber=True):
        if urls:
            video_dir = cls._make_output_directory(
                class_name, unit_name, video_type)
            if autonumber:
                name_template = '{}-{}'.format('%(autonumber)d', cls.video_name_template)
            else:
                name_template = cls.video_name_template
            youtubedl_options = {
                'outtmpl' : os.path.join(video_dir, name_template),
                'quiet': cls.disable_youtubedl_output,
            }
            with youtube_dl.YoutubeDL(youtubedl_options) as downloader:
                downloader.download(urls)
