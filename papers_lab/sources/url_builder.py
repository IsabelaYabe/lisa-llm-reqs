from __future__ import annotations

from typing import List, Tuple, Dict, Optional
from urllib.parse import urlparse, urlencode, quote, quote_plus

from ..config import ACM_SEARCH_BASE, IEEE_SEARCH_BASE

def build_acm_search_url(
    groups: List[Tuple[str, List[str]]],
    after: Tuple[int, int] = (2022, 1),
    before: Tuple[int, int] = (2026, 1),
    exclude_filters: List[Tuple[str, List[str]]] | None = None,
) -> str:
    """
    Build a search URL for the ACM Digital Library with given search groups and date range.
    """
    params: Dict[str, object] = {
        "fillQuickSearch": "false",
        "target": "advanced",
        "expand": "dl",
        "AfterMonth": after[1],
        "AfterYear": after[0],
        "BeforeMonth": before[1],
        "BeforeYear": before[0],
    }

    field_index = 1
    for field, terms in groups:
        params[f"field{field_index}"] = field
        params[f"text{field_index}"]  = "(" + " OR ".join(f'"{t}"' for t in terms) + ")"
        field_index += 1

    if exclude_filters:
        for field, terms in exclude_filters:
            params[f"field{field_index}"] = field
            params[f"text{field_index}"]  = "NOT (" + " OR ".join(f'"{t}"' for t in terms) + ")"
            field_index += 1

    return f"{ACM_SEARCH_BASE}?{urlencode(params, quote_via=quote_plus)}"
    
def build_ieee_search_url(
    groups: List[Tuple[str, List[str]]],
    year_range: Tuple[int, int] = (2022, 2025),
    exclude_filters: List[Tuple[str, List[str]]] | None = None,  
) -> str:
    """
    Build a search URL for the IEEE Xplore Digital Library with given search groups and year range.
    """

    include_parts = [
        "(" + " OR ".join(f'"{field}":"{t}"' for t in terms) + ")"
        for field, terms in groups
    ]

    if exclude_filters:
        include_parts += [
            "NOT (" + " OR ".join(f'"{field}":"{t}"' for t in terms) + ")"
            for field, terms in exclude_filters
        ]

    query_text = " AND ".join(include_parts)

    params = {
        "action": "search",
        "newsearch": "true",
        "matchBoolean": "true",
        "queryText": query_text,
        "ranges": f"{year_range[0]}_{year_range[1]}_Year",
    }
    return f"{IEEE_SEARCH_BASE}?{urlencode(params, quote_via=quote)}"

def build_search_urls_for_sources(groups: List[Tuple[str, List[str]]],
    year_range: Tuple[int, int],
    exclude_filters: List[Tuple[str, List[str]]] | None
) -> Tuple[str, str]:
    """
    Build search URLs for both IEEE and ACM sources based on the provided groups, year range, and optional exclude filters.
    """
    start, end = year_range
    if exclude_filters:
        ieee_url = build_ieee_search_url(groups, year_range, exclude_filters)
        acm_url  = build_acm_search_url(groups, (start, 1), (end + 1, 1), exclude_filters) 
    else:
        ieee_url = build_ieee_search_url(groups, year_range)
        acm_url  = build_acm_search_url(groups, (start, 1), (end + 1, 1))         
    return ieee_url, acm_url