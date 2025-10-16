import time
from logger import logger

from papers_lab.sources.url_builder import build_search_urls_for_sources
from papers_lab.sources.orchestrator import SourcesOrchestrator
from papers_lab.io import Storage

year_range = (2015, 2026)

# exclude_noise = [
    # ("Abstract", [
        # "circuit","hardware reverse engineering",
        # "malware","virus","exploit","firmware","embedded systems","binary", "bytecode"
    # ])
# ]

abstract_reverse_engineering = ("Abstract", ["reverse engineering" , "design recovery"])

abstract_requirements = ("Abstract", ["use case", "UML", "requirements"])

abstract_nlp = ("Abstract", ["LLM", "static analysis", "natural language processing", "NLP"])

abstract_others = ("Abstract", ["object-oriented", "software modeling"])

groups_sets = {
    # "search_1": [abstract_reverse_engineering, abstract_requirements, abstract_others],
    "search_2": [abstract_reverse_engineering, abstract_requirements, abstract_nlp]
}

# (Abstract:("reverse engineering" OR "design recovery"))
# AND (Abstract:("object-oriented" OR "UML" OR "software modeling"))
# AND (Abstract:("use case" OR "requirements"))
# https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&matchBoolean=true&newsearch=true&queryText=((Abstract:(%22reverse%20engineering%22%20OR%20%22design%20recovery%22))%0AAND%20(Abstract:(%22object-oriented%22%20OR%20%22UML%22%20OR%20%22software%20modeling%22))%0AAND%20(Abstract:(%22use%20case%22%20OR%20%22requirements%22))%0A)


# (Abstract:("reverse engineering" OR "design recovery"))
# AND (Abstract:("object-oriented" OR "UML" OR "software modeling"))
# AND (Abstract:("LLM" OR "static analysis" OR "natural language processing" OR "NLP"))

# https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&matchBoolean=true&queryText=((Abstract:(%22reverse%20engineering%22%20OR%20%22design%20recovery%22))%0AAND%20(Abstract:(%22object-oriented%22%20OR%20%22UML%22%20OR%20%22software%20modeling%22))%0AAND%20(Abstract:(%22LLM%22%20OR%20%22static%20analysis%22%20OR%20%22natural%20language%20processing%22%20OR%20%22NLP%22))%0A)&highlight=true&returnFacets=ALL&returnType=SEARCH&matchPubs=true&ranges=2023_2025_Year

def main():
    start_time = time.time()
    storage = Storage()
    orch = SourcesOrchestrator(storage) 

    for name, groups in groups_sets.items():
        # ieee_url, acm_url = build_search_urls_for_sources(groups, year_range, exclude_noise)
        ieee_url, acm_url = build_search_urls_for_sources(groups, year_range)
        logger.debug(f"[{name}] IEEE URL: {ieee_url}")
        logger.debug(f"[{name}] ACM URL: {acm_url}")
        # urls = [ieee_url, acm_url]
        # urls = [ieee_url]
        urls = [acm_url]

        logger.debug(f"[{name}] Starting search…")
        # saved_ieee, saved_acm = orch.fetch_all(urls, research_tag=name, save_dir="search_data")
        saved_ieee, saved_acm = orch.fetch_all(urls, research_tag=name, save_dir="ieee_data_test")

        logger.debug(f"[{name}] IEEE saved: {len(saved_ieee)} | ACM saved: {len(saved_acm)}")

    elapsed = time.time() - start_time
    logger.debug(f"Total execution time: {elapsed:.2f} s")

if __name__ == "__main__":
    main()