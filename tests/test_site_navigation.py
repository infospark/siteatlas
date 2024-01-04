import os
from typing import Generator

import pytest
from _pytest.fixtures import fixture
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from siteatlas.site_nagivation import get_page_map, get_site_map, SiteMap

CURRENT_LOCATION = os.path.dirname(os.path.realpath(__file__))
TEST_RESOURCES = os.path.join(CURRENT_LOCATION, 'resources/sample_basic_website')


def test_merge_two_site_maps() -> None:
    # Given two site maps
    site_map_1 = SiteMap({'a', 'b', 'c'}, {'1', '2', '3'})
    site_map_2 = SiteMap({'c', 'd', 'e'}, {'3', '4', '5'})
    # When I merge them
    merged_site_map = site_map_1.combine_site_maps(site_map_2)
    # Then I expect to get a new site map with all the urls from both site maps
    assert merged_site_map.urls == {'a', 'b', 'c', 'd', 'e'}
    assert merged_site_map.ignored_urls == {'1', '2', '3', '4', '5'}


def test_get_page_map() -> None:
    # Given a page of html
    with open(f'{os.path.join(TEST_RESOURCES, "index.html")}', 'r') as f:
        html = f.read()
    # When I get the links from the page
    page_map = get_page_map(html=html,
                            base_url=f'file://{TEST_RESOURCES}/index.html',
                            allowed_domains={""})

    assert isinstance(page_map, SiteMap)
    # Then I expect to get a list of urls that are linked to from the page
    assert len(page_map.urls) == 2
    # And I expect to get the correct urls
    assert f'file://{TEST_RESOURCES}/about.html' in page_map.urls
    assert f'file://{TEST_RESOURCES}/contact.html' in page_map.urls
    # And I expect the Google url to be disallowed
    assert 'https://www.google.com/search' in page_map.ignored_urls


def test_links_from_page_allow_extra_domain() -> None:
    # Given a page of html
    with open(f'{os.path.join(TEST_RESOURCES, "index.html")}', 'r') as f:
        html = f.read()
    # When I get the links from the page
    page_map = get_page_map(html,
                            f'file://{TEST_RESOURCES}/index.html',
                            allowed_domains={'', 'www.google.com'})
    # Then I expect to get a list of urls that are linked to from the page
    assert len(page_map.urls) == 3
    # And I expect to get the correct urls
    assert f'file://{TEST_RESOURCES}/about.html' in page_map.urls
    assert f'file://{TEST_RESOURCES}/contact.html' in page_map.urls
    assert 'https://www.google.com/search' in page_map.urls
    assert len(page_map.ignored_urls) == 0

@pytest.mark.integration("Requires Selenium")
def test_site_navigation_file_url(driver: WebDriver) -> None:
    # Given a 'seed' url for a website
    index_url = f'file://{os.path.join(TEST_RESOURCES, "index.html")}'
    # When I generate a site map
    site_map = get_site_map(index_url, driver, allowed_domains={''})
    assert isinstance(site_map, SiteMap)

    # Then I expect to get a list of urls that are linked to from the seed url
    assert len(site_map.urls) == 4
    assert f'file://{os.path.join(TEST_RESOURCES, "about.html")}' in site_map.urls
    assert f'file://{os.path.join(TEST_RESOURCES, "contact.html")}' in site_map.urls
    assert f'file://{os.path.join(TEST_RESOURCES, "index.html")}' in site_map.urls
    assert f'file://{os.path.join(TEST_RESOURCES, "founder_profile.html")}' in site_map.urls
    # Ensure we don't follow links that lead to other domains
    assert 'https://www.google.com/search' not in site_map.urls

    # Ensure that the Google URL IS in the disallowed urls
    assert 'https://www.google.com/search' in site_map.ignored_urls


@pytest.mark.integration("Interacts with a live website")
def test_get_site_map_live_url(driver: WebDriver) -> None:
    # When I provide a seed URL
    url = 'https://choosealicense.com'
    # And one additional allowed site
    allowed_domains = {'choosealicense.com', 'opensource.guide'}
    # Then I recursively follow all internal links
    site_map = get_site_map(url, driver, allowed_domains=allowed_domains)

    # Until all internal URLs have been exhausted
    assert len(site_map.urls) > 1
    assert 'https://choosealicense.com/community/' in site_map.urls
    assert 'https://opensource.guide/legal/' in site_map.urls

    disallowed_domains = site_map.get_ignored_url_domains()
    assert len(disallowed_domains) > 0
    assert 'github.com' in disallowed_domains


@fixture
def driver() -> Generator[WebDriver, None, None]:
    driver = webdriver.Chrome()
    yield driver
    driver.quit()
