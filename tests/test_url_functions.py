from siteatlas.url_functions import get_scheme_and_fully_qualified_domain_and_path, get_absolute_url, \
    get_fully_qualified_domain_name, get_domain_and_suffix, get_scheme_and_fully_qualified_domain


def test_get_absolute_url() -> None:
    # Given a file url
    base_url = 'file://files/tests/index.html'
    # and a relative url
    relative_url = 'about.html'
    # When I get the absolute url
    absolute_url = get_absolute_url(base_url, relative_url)
    # Then I expect to get the absolute url
    assert absolute_url == 'file://files/tests/about.html'

    # Given a http url
    base_url = 'https://www.google.com/'
    # and a relative url
    relative_url = 'search.html'
    # When I get the absolute url
    absolute_url = get_absolute_url(base_url, relative_url)
    # Then I expect to get the absolute url
    assert absolute_url == 'https://www.google.com/search.html'

    # Given a http url that contains a fragment
    base_url = 'https://www.google.com/search.html#fragment'
    # and a relative url
    relative_url = 'home.html'
    # When I get the absolute url
    absolute_url = get_absolute_url(base_url, relative_url)
    # Then I expect the absolute url to NOT include the fragment
    assert absolute_url == 'https://www.google.com/home.html'

    # Given a http url that contains a query
    base_url = 'https://www.google.com/search.html?x=1&y=2'
    # and a relative url
    relative_url = 'home.html'
    # When I get the absolute url
    absolute_url = get_absolute_url(base_url, relative_url)
    # Then I expect the absolute url to NOT include the fragment
    assert absolute_url == 'https://www.google.com/home.html'

    # Given a relative url that is just root
    base_url = 'https://www.google.com/search.html?x=1&y=2#wibble'
    # and a relative url
    relative_url = '/'
    # When I get the absolute url
    absolute_url = get_absolute_url(base_url, relative_url)
    # Then I expect the absolute url to NOT include the fragment
    assert absolute_url == 'https://www.google.com/'

    # Given a URL that contains a fragment
    base_url = 'https://www.glenwoodhouse.co.za/admissions'
    relative_url = '#dm'
    # When I get the absolute url
    absolute_url = get_absolute_url(base_url, relative_url)
    # Then I expect the absolute url to NOT include the fragment
    assert absolute_url == 'https://www.glenwoodhouse.co.za/admissions'

def test_get_domain_name_versions() -> None:
    # Given a url with a http schema and domain and path
    http_url = 'https://www.google.com/wibble/wobble'
    # When I extract the domain from the url
    fqdn = get_fully_qualified_domain_name(http_url)
    # Then I expect to get the domain
    assert fqdn == 'www.google.com'

    # When I get the domain with suffix
    ds = get_domain_and_suffix(http_url)
    # Then I expect to get the domain with suffix
    assert ds == 'google.com'


def test_get_scheme_and_domain_from_http_url() -> None:
    # Given an url with a http schema and domain and path
    http_url = 'https://www.google.com/wibble/wobble'
    # When I get the scheme and domain from the url
    scheme_and_domain = get_scheme_and_fully_qualified_domain(http_url)
    # Then I expect to get the scheme and domain
    assert scheme_and_domain == 'https://www.google.com'

    # Given an url with a http schema and domain only
    http_url = 'https://www.google.com/'
    # When I get the scheme and domain from the url
    scheme_and_domain = get_scheme_and_fully_qualified_domain(http_url)
    # Then I expect to get the scheme and domain
    assert scheme_and_domain == 'https://www.google.com'


def test_get_scheme_and_domain_from_file_url() -> None:
    # Given a file url with a file at the end
    file_url = 'file:///Users/username/PycharmProjects/sample_basic_website/index.html'
    # When I get the scheme and domain from the url
    scheme_and_domain = get_scheme_and_fully_qualified_domain_and_path(file_url)
    # Then I expect to get the scheme and domain
    assert scheme_and_domain == 'file:///Users/username/PycharmProjects/sample_basic_website'

    # Given a file url with a directory at the end
    file_url = 'file:///Users/username/PycharmProjects/sample_basic_website/'
    # When I get the scheme and domain from the url
    scheme_and_domain = get_scheme_and_fully_qualified_domain_and_path(file_url)
    # Then I expect to get the scheme and domain
    assert scheme_and_domain == 'file:///Users/username/PycharmProjects/sample_basic_website'


def test_strip_query_and_fragment_from_url() -> None:
    # Given an url with a query and fragment
    test_url = 'https://www.google.com/wibble/wobble?query=1&query2=2#fragment'
    # When I strip the query and fragment from the url
    stripped_url = get_scheme_and_fully_qualified_domain_and_path(test_url)
    # Then I expect to get the url without the query and fragment
    assert stripped_url == 'https://www.google.com/wibble/wobble'

def test_get_scheme_and_fully_qualified_domain_name() -> None:
    # Given a urls with a path, a query and a fragment
    test_url = 'https://www.google.com/wibble/wobble?query=1&query2=2#fragment'
    # When I strip the query and fragment from the url
    stripped_url = get_scheme_and_fully_qualified_domain(test_url)
    # Then I expect to get the url without the query and fragment
    assert stripped_url == 'https://www.google.com'
