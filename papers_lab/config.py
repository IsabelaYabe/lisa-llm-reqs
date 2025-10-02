import re

# ==================== REGEX PATTERNS ====================
DOI_PATTERN = re.compile(r"^10\.\S+", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"(\d{4})\s*$", re.IGNORECASE) 
MONTH_PATTERN = re.compile(r"([A-Za-z]+)\s+\d{4}\s*$", re.IGNORECASE)
YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")

# ==================== MAPEAMENTOS ====================
MONTH_MAPPING = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

# ==================== URL BASES ====================
ACM_SEARCH_BASE = "https://dl.acm.org/action/doSearch"
IEEE_SEARCH_BASE = "https://ieeexplore.ieee.org/search/searchresult.jsp"