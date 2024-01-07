import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Union, List

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from siteatlas.url_functions import get_fully_qualified_domain_name, get_absolute_url


@dataclass
class SiteMap:
    urls: set[str] = field(default_factory=set)
    ignored_urls: set[str] = field(default_factory=set)

    def diff_site_maps(self, other: 'SiteMap') -> 'SiteMap':
        urls_diff = self.urls = self.urls.difference(other.urls)
        ignored_urls_diff = self.ignored_urls.difference(other.ignored_urls)
        return SiteMap(urls_diff, ignored_urls_diff)

    def get_ignored_url_domains(self) -> set[str]:
        return {get_fully_qualified_domain_name(url) for url in self.ignored_urls}

    def __add__(self, other: 'SiteMap') -> 'SiteMap':
        combined_urls = self.urls.union(other.urls)
        combined_ignored_urls = self.ignored_urls.union(other.ignored_urls)
        return SiteMap(combined_urls, combined_ignored_urls)


def get_element_hash(driver: WebDriver, element):  # type: ignore
    inner_html = driver.execute_script("return arguments[0].outerHTML;", element)  # type: ignore
    return hashlib.md5(inner_html.encode()).hexdigest()


def get_button_targets(driver: WebDriver,
                       allowed_domains: set[str]) -> SiteMap:
    # Attempt to find all buttons on the page
    button_urls = set()
    base_url = driver.current_url

    buttons_seen = []
    # find the next unseen button

    more_buttons = True
    while more_buttons:
        all_buttons = driver.find_elements(By.TAG_NAME, 'button')
        next_button = [button for button in all_buttons if get_element_hash(driver, button) not in buttons_seen]
        if next_button:
            button = next_button[0]
            try:
                # scroll the button into view
                buttons_seen.append(get_element_hash(driver, button))
                driver.execute_script("arguments[0].scrollIntoView();", button)  # type: ignore
                # click the button via execute script
                # JavaScript to create and dispatch the event
                mousedown_script = """
                var targetElement = arguments[0];
                var mouseDownEvent = document.createEvent('MouseEvents');
                mouseDownEvent.initMouseEvent(
                    'mousedown', true, true, window, 0, 0, 0, 0, 0, 
                    false, false, false, false, 0, null
                );
                targetElement.dispatchEvent(mouseDownEvent);
                """
                # Execute the script
                driver.execute_script(mousedown_script, button)  # type: ignore
                time.sleep(0.25)
                if driver.current_url != base_url:
                    button_urls.add(driver.current_url)
                    driver.get(base_url)
            except Exception as e:
                logging.info(f"Could not click on button got {e}")
        else:
            more_buttons = False

    urls = {url for url in button_urls if get_fully_qualified_domain_name(url) in allowed_domains}
    # Return the buttons as a list of urls
    return SiteMap(set(urls), set())


def get_links_map(html: str,
                  base_url: str,
                  allowed_domains: set[str]) -> SiteMap:
    """Get a links from a single page."""
    # Create a BeautifulSoup object from the html
    page_soup = BeautifulSoup(html, 'html.parser')
    # Find all the links in the html
    link_tags = page_soup.findAll('a')
    urls = set([str(link['href']) for link in link_tags if 'href' in link.attrs])

    # map relative links to absolute links
    absolute_urls = set()
    for url in urls:
        absolute_urls.add(get_absolute_url(base_url, url))

    urls = {url for url in absolute_urls if get_fully_qualified_domain_name(url) in allowed_domains}
    ignored_urls = absolute_urls.difference(urls)

    logging.info(f"Found {len(urls)} allowed urls and {len(ignored_urls)} disallowed urls in {base_url}")
    # Return the links as a list of urls
    return SiteMap(urls, ignored_urls)


def get_site_map(url: Union[str, List[str]],
                 driver: WebDriver,
                 site_map: SiteMap = SiteMap(),
                 current_depth: int = 0,
                 max_depth: int = 10,
                 allowed_domains: Optional[set[str]] = None,
                 wait_in_seconds: float = 0.1) -> SiteMap:
    """Map a whole site."""
    if not isinstance(url, list):
        url = [url]

    if not allowed_domains:
        allowed_domains = set()

    result = SiteMap()

    for single_url in url:
        # If allowed_domains does not include the current domains then add it
        if get_fully_qualified_domain_name(single_url) not in allowed_domains:
            allowed_domains.add(get_fully_qualified_domain_name(single_url))

        site_map = get_site_map_recursive(url=single_url,
                                          driver=driver,
                                          site_map=site_map,
                                          allowed_domains=allowed_domains,
                                          current_depth=current_depth,
                                          max_depth=max_depth,
                                          wait_in_seconds=wait_in_seconds)
        result = result + site_map

    return result


def get_site_map_recursive(url: str,
                           driver: WebDriver,
                           site_map: SiteMap,
                           allowed_domains: set[str],
                           current_depth: int,
                           max_depth: int,
                           wait_in_seconds: float) -> SiteMap:
    """Map a whole site."""
    logging.info(f"Starting get_site_map map for {url} at depth {current_depth}")

    if max_depth and current_depth >= max_depth:
        return site_map

    driver.get(url)
    time.sleep(wait_in_seconds)
    html = driver.page_source

    # Add self to all
    site_map.urls.add(url)

    # Get any new links from the page
    links_map = get_links_map(html, url, allowed_domains)

    # Get any new links via buttons
    buttons_map = get_button_targets(driver, allowed_domains)

    new_map = buttons_map + links_map

    # Get any new (unseen) urls for recursion
    unseen_site_map = new_map.diff_site_maps(site_map)

    # Add new links to all_links
    site_map = site_map + new_map

    # Recursively call get_site_map for each new link
    for unseen_url in unseen_site_map.urls:
        unseen_site_map = get_site_map_recursive(url=unseen_url,
                                                 driver=driver,
                                                 site_map=site_map,
                                                 current_depth=current_depth + 1,
                                                 max_depth=max_depth,
                                                 allowed_domains=allowed_domains,
                                                 wait_in_seconds=wait_in_seconds)
        site_map = site_map + unseen_site_map

    logging.info(f"Completed get_site_map for {url} at depth {current_depth} "
                 f"with {len(site_map.urls)} allowed urls "
                 f"and {len(site_map.ignored_urls)} disallowed urls")
    return site_map
