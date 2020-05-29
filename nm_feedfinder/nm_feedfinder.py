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


def feeds(address: str) -> List[str]:
    # Python dictionaries are ordered so this serves us as an ordered set.
    links = {}

    url = urlparse(address)
    path = PurePosixPath(unquote(url.path))

    # Given a url (e.g. http://example.com/a/b/c/) climb up the path
    # and check at each level for a feed.
    urls = [url]
    for parent in path.parents:
        url = url._replace(path=str(parent))
        urls.append(url)

    # Take advantage of HTTP persistent connections to speed up multiple
    # requests to the same host
    with requests.Session() as sesh:
        for url_ in urls:
            links_ = find_links(sesh, url_)
            if links_:
                # A longer way of saying "extend"
                links.update(dict.fromkeys(links_))

    return list(links.keys())


def find_links(sesh: requests.Session, url: ParseResult) -> List[str]:
    links = []

    try:
        response = sesh.get(urlunparse(url), timeout=3)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    soup = BeautifulSoup(response.text, features="lxml")

    # Check if the URL itself might be the URL of a feed
    if could_be_feed_text(response.text):
        return urlunparse(url)

    # Check for Atom/RSS autodiscovery using <link> elements
    links_ = try_link_alternate(url, soup)
    if links_:
        links.extend(links_)

    # Check for the most common paths
    links_ = try_common_paths(sesh, url)
    if links_:
        links.extend(links_)

    # Check for all the hyperlinks on the page that looks like a feed link
    links_ = try_hrefs(sesh, url, soup)
    if links_:
        links.extend(links_)

    return links


def try_link_alternate(url: ParseResult, soup: BeautifulSoup) -> List[str]:
    """
    Tries finding <link rel="alternate" type="application/rss+xml" href="..." /> element,
    which is the semantic way.
    """
    links = []

    atom_link = soup.find("link", {"rel": "alternate", "type": "application/atom+xml"})
    if atom_link is not None:
        links.append(urljoin(urlunparse(url), atom_link.attrs["href"]))

    rss_link = soup.find("link", {"rel": "alternate", "type": "application/rss+xml"})
    if rss_link is not None:
        links.append(urljoin(urlunparse(url), rss_link.attrs["href"]))

    return links


def try_common_paths(sesh: requests.Session, url: ParseResult) -> List[str]:
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
        if could_be_feed(sesh, feed_url):
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
        response = sesh.get(url)
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
    return url.endswith(".xml") or url.endswith(".rdf") or url.endswith(".xml") or url.endswith(
        ".atom") or "feed" in url or "rss" in url


if __name__ == "__main__":
    import sys

    urls = feeds(sys.argv[1]) or []
    for url in urls:
        print(url)
