"""Main module for running the Gumtree scrapers."""

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from gumtree_scraper.spiders.properties import PropertiesSpider


def main():
    """Main function"""
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(PropertiesSpider)
    process.start()


if __name__ == "__main__":
    main()
