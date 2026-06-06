from dataclasses import dataclass


@dataclass
class Article:
    source: str
    title: str
    url: str
    description: str
