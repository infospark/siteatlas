from urllib.parse import urlparse, urljoin, urldefrag

import tldextract


# Helper function to get the scheme and domain from an url
def get_scheme_and_fully_qualified_domain_and_path(url: str) -> str:
    parsed_url = urlparse(url)
    if parsed_url.scheme == 'file':
        path = parsed_url.path
        # If the path ends with a filename (contains a dot) then remove it
        last_path_component = path.split('/')[-1]
        if '.' in last_path_component:
            path = path.rsplit('/', 1)[0]
        # Remove any trailing slashes
        if path.endswith('/'):
            path = path[:-1]
        return f"{parsed_url.scheme}://{path}"
    else:
        return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"


def get_scheme_and_fully_qualified_domain(url: str) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def get_domain_and_suffix(url: str) -> str:
    tld = tldextract.extract(url)
    return f"{tld.domain}.{tld.suffix}"


def get_fully_qualified_domain_name(url: str) -> str:
    parsed_url = urlparse(url)
    return parsed_url.netloc

def get_absolute_url(base_url: str, relative_url: str) -> str:
    absolute_url = urljoin(base_url, relative_url)
    # strip any fragments from the resulting URL
    absolute_url, _ = urldefrag(absolute_url)
    return absolute_url
