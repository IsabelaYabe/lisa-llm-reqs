from __future__ import annotations

from dataclasses import dataclass, field 
from typing import Optional, List, Dict

@dataclass
class ResearchPaper:
    title: str
    date: Optional[str]
    abstract: Optional[str]  
    DOI: Optional[str]
    source_url: str
    authors: Optional[List[str]] = field(default_factory=List)
    keywords: Optional[List[str]] = field(default_factory=List)
    
@dataclass
class Research:
    num_results: int 
    keywords: str 
    years: str 
    publisher: str 
    url: str
    content_type: List[str] = field(default_factory=List) 
    papers_urls: List[str] = field(default_factory=List) 
    failed_urls: List[str] = field(default_factory=List)
    papers: Dict = field(default_factory=Dict)
    incomplete_papers: Dict = field(default_factory=Dict) 
