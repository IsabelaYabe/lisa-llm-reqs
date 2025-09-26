from __future__ import annotations
from dataclasses import dataclass, field 
from typing import Optional

@dataclass
class ResearchPaper:
    title: str
    date: Optional[str]
    abstract: Optional[str]  
    DOI: Optional[str]
    source_url: str
    authors: Optional[list[str]] = field(default_factory=list)
    keywords: Optional[list[str]] = field(default_factory=list)
    
@dataclass
class Research:
    num_results: int 
    keywords: str 
    years: str 
    publisher: str 
    url: str
    content_type: list[str] = field(default_factory=list) 
    papers_urls: list[str] = field(default_factory=list) 
    failed_urls: list[str] = field(default_factory=list)
    papers: dict = field(default_factory=dict)
    incomplete_papers: dict = field(default_factory=dict) 
