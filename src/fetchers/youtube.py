import xml.etree.ElementTree as ET

import requests

from fetchers import Article

YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}


def fetch(channel_ids: list[str], max_items: int = 10) -> list[Article]:
    if not channel_ids:
        return []
    per_channel = max(1, max_items // len(channel_ids))
    articles = []
    for channel_id in channel_ids:
        resp = requests.get(YOUTUBE_RSS.format(channel_id), timeout=10)
        root = ET.fromstring(resp.text)
        entries = root.findall("atom:entry", NS)[:per_channel]
        for entry in entries:
            title = entry.findtext("atom:title", namespaces=NS) or ""
            link_el = entry.find("atom:link", NS)
            url = link_el.get("href", "") if link_el is not None else ""
            desc_el = entry.find("media:group/media:description", NS)
            description = ((desc_el.text or "") if desc_el is not None else "")[:200]
            if title and url:
                articles.append(Article(source="YouTube", title=title, url=url, description=description))
    return articles
