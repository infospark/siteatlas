import logging
from dataclasses import dataclass, field
import time
from typing import Optional

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver

from siteatlas.url_functions import get_domain, get_absolute_url


@dataclass
class SiteMap:
    urls: set[str] = field(default_factory=set)
    ignored_urls: set[str] = field(default_factory=set)

    def combine_site_maps(self, other: 'SiteMap') -> 'SiteMap':
        combined_urls = self.urls.union(other.urls)
        combined_ignored_urls = self.ignored_urls.union(other.ignored_urls)
        return SiteMap(combined_urls, combined_ignored_urls)

    def diff_site_maps(self, other: 'SiteMap') -> 'SiteMap':
        urls_diff = self.urls = self.urls.difference(other.urls)
        ignored_urls_diff = self.ignored_urls.difference(other.ignored_urls)
        return SiteMap(urls_diff, ignored_urls_diff)

    def get_ignored_url_domains(self) -> set[str]:
        return {get_domain(url) for url in self.ignored_urls}


def get_page_map(html: str,
                 base_url: str,
                 allowed_domains: set[str]) -> SiteMap:
    # Create a BeautifulSoup object from the html
    page_soup = BeautifulSoup(html, 'html.parser')
    # Find all the links in the html
    link_tags = page_soup.findAll('a')
    urls = set([str(link['href']) for link in link_tags if 'href' in link.attrs])

    # map relative links to absolute links
    absolute_urls = set()
    for url in urls:
        absolute_urls.add(get_absolute_url(base_url, url))

    urls = {url for url in absolute_urls if get_domain(url) in allowed_domains}
    ignored_urls = absolute_urls.difference(urls)

    logging.info(f"Found {len(urls)} allowed urls and {len(ignored_urls)} disallowed urls in {base_url}")
    # Return the links as a list of urls
    return SiteMap(urls, ignored_urls)


def get_site_map(url: str,
                 driver: WebDriver,
                 site_map: SiteMap = SiteMap(),
                 current_depth: int = 0,
                 max_depth: Optional[int] = None,
                 allowed_domains: Optional[set[str]] = None,
                 default_wait_in_seconds: float = 0.1) -> SiteMap:
    logging.info(f"Starting get_site_map map for {url} at depth {current_depth}")

    if max_depth and current_depth >= max_depth:
        return site_map

    if not site_map:
        site_map = SiteMap()

    if not allowed_domains:
        allowed_domains = set()

    driver.get(url)
    time.sleep(default_wait_in_seconds)
    html = driver.page_source

    # Add self to all
    site_map.urls.add(url)

    # Get any new links from the page
    page_map = get_page_map(html, url, allowed_domains)

    # Get any new (unseen) urls for recursion
    unseen_site_map = page_map.diff_site_maps(site_map)

    # Add new links to all_links
    site_map = site_map.combine_site_maps(page_map)

    # Recursively call get_site_map for each new link
    for unseen_url in unseen_site_map.urls:
        unseen_site_map = get_site_map(url=unseen_url,
                                       driver=driver,
                                       site_map=site_map,
                                       current_depth=current_depth + 1,
                                       max_depth=max_depth,
                                       allowed_domains=allowed_domains)
        site_map = site_map.combine_site_maps(unseen_site_map)

    logging.info(f"Completed get_site_map for {url} at depth {current_depth} "
                 f"with {len(site_map.urls)} allowed urls "
                 f"and {len(site_map.ignored_urls)} disallowed urls")
    return site_map
