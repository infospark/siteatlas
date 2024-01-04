from urllib.parse import urlparse, urljoin, urldefrag


# Helper function to get the scheme and domain from an url
def get_scheme_and_domain(url: str, include_path: bool = False) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path if include_path else ''}"


def get_scheme_and_domain_and_path(url: str) -> str:
    return get_scheme_and_domain(url, True)


def get_domain(url: str) -> str:
    parsed_url = urlparse(url)
    return parsed_url.netloc


def get_absolute_url(base_url: str, relative_url: str) -> str:
    absolute_url = urljoin(base_url, relative_url)
    # strip any fragments from the resulting URL
    absolute_url, _ = urldefrag(absolute_url)

    return absolute_url
