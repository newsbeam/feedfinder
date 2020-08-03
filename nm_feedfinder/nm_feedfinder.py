# nm_feedfinder - find Atom/RSS links of a website given a URL
#
# Usage:
#     nm_feedfinder.feeds("https://blog.newsmail.today/")
#   or from command line:
#     python3 nm_feedfinder.py https://blog.newsmail.today/
#
# Heavily inspired by feedfinder:
# http://www.aaronsw.com/2002/feedfinder/

from typing import List
from urllib.parse import ParseResult, urljoin, unquote, urlparse, urlunparse
from pathlib import PurePosixPath

from bs4 import BeautifulSoup
import requests

TIMEOUT = 3


def feeds(address: str, exhaust: bool = True, climb: bool = True) -> List[str]:
    """
    Given a url (e.g. http://example.com/a/b/c/) optionally climb up the path:

    1. http://example.com/a/b/c/ (the input itself)
    2. http://example.com/a/b/
    3. http://example.com/a
    4. http://example.com/

    ...and at each level check for possible locations for a feed:

    1. Auto-discovery links
         
       `<link rel="alternate" type="application/X+xml" href="..." />`
    2. Common paths
      
       E.g. `/feed`, `/rss` `/atom`, `/feed.xml`, `/atom.xml`, `/rss.xml`,
       `/index.atom`, `/index.rdf`, `/index.rss`, `/index.xml`, ...
    3. Hyperlinks to what might be a feed

       <a href="...">

    :param address: The URL to begin with.
    :param exhaust: Controls whether all the possible locations, at each level, shall be exhausted.
    :param climb: Controls whether the URL paths shall be climbed up.
    :return: A list of links to feeds, possibly empty.
    """
    links = []

    url = urlparse(address)
    path = PurePosixPath(unquote(url.path))

    urls = [url]
    if climb:
        for parent in path.parents:
            url = url._replace(path=str(parent))
            urls.append(url)

    # Take advantage of HTTP persistent connections to speed up multiple
    # requests to the same host
    with requests.Session() as sesh:
        for url_ in urls:
            for link in find_links(sesh, url_, exhaust):
                if link not in links:
                    links.append(link)

    return links


def find_links(sesh: requests.Session, url: ParseResult, exhaust: bool = True) -> List[str]:
    links = []

    try:
        response = sesh.get(urlunparse(url), timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    soup = BeautifulSoup(response.text, features="lxml")

    # Check if the URL itself might be the URL of a feed
    if could_be_feed_text(response.text):
        return urlunparse(url)

    # Check for Atom/RSS auto-discovery using <link> elements
    links_ = try_link_alternate(url, soup, exhaust)
    if links_:
        if not exhaust:
            return links_
        links.extend(links_)

    # Check for the most common paths
    links_ = try_common_paths(sesh, url, exhaust)
    if links_:
        if not exhaust:
            return links_
        links.extend(links_)

    # Check for all the hyperlinks on the page that looks like a feed link
    links_ = try_hrefs(sesh, url, soup)
    if links_:
        if not exhaust:
            return links_
        links.extend(links_)

    return links


def try_link_alternate(url: ParseResult, soup: BeautifulSoup, exhaust: bool = True) -> List[str]:
    """
    Tries finding <link rel="alternate" type="application/rss+xml" href="..." /> element,
    which is the semantic way.
    """
    links = []

    atom_link = soup.find("link", {"rel": "alternate", "type": "application/atom+xml"})
    if atom_link is not None:
        href = urljoin(urlunparse(url), atom_link.attrs["href"])
        if not exhaust:
            return [href]
        links.append(href)

    rss_link = soup.find("link", {"rel": "alternate", "type": "application/rss+xml"})
    if rss_link is not None:
        href = urljoin(urlunparse(url), rss_link.attrs["href"])
        if not exhaust:
            return [href]
        links.append(href)

    return links


def try_common_paths(sesh: requests.Session, url: ParseResult, exhaust: bool = False) -> List[str]:
    common_paths = [
        "feed",
        "rss",
        "atom",
        "feed.xml",
        "atom.xml",
        "rss.xml",
        "index.atom",
        "index.rdf",
        "index.rss",
        "index.xml",
    ]

    links = []
    for path in common_paths:
        feed_url = urljoin(urlunparse(url), path)
        if not could_be_feed(sesh, feed_url):
            continue
        if not exhaust:
            return [feed_url]
        links.append(feed_url)

    return links


def try_hrefs(sesh: requests.Session, url: ParseResult, soup: BeautifulSoup) -> List[str]:
    links = []
    as_ = soup.find_all("a", href=True)
    urls = [urljoin(urlunparse(url), l.attrs["href"]) for l in as_]  # type: List[str]

    for feed_url in filter(is_url_feedlike, urls):
        if could_be_feed(sesh, feed_url):
            links.append(feed_url)

    return links


def could_be_feed(sesh: requests.Session, url: str) -> bool:
    try:
        response = sesh.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return False

    return bool(could_be_feed_text(response.text))


def could_be_feed_text(data) -> bool:
    # From feedfinder
    # http://www.aaronsw.com/2002/feedfinder/
    data = data.lower()
    if data.count("<html"):
        return False
    return bool(data.count("<rss") + data.count("<rdf") + data.count("<feed"))


def is_url_feedlike(url: str) -> bool:
    return url.endswith(".xml") or url.endswith(".rdf") or url.endswith(".rss") or url.endswith(
        ".atom") or "feed" in url or "rss" in url or "atom" in url


if __name__ == "__main__":
    import sys

    urls = feeds(sys.argv[1]) or []
    for url in urls:
        print(url)
