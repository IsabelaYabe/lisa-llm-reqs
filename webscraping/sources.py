from logger import logger
from webscraping.web_driver_config import *
import pickle
import os
from urllib.parse import urlparse
from urllib.parse import urlencode, quote, quote_plus

def build_acm_search_url(
    groups: list[tuple[str, list[str]]],
    after: tuple[int, int] = (2022, 1),
    before: tuple[int, int] = (2026, 1),
    exclude_filters: list[tuple[str, list[str]]] | None = None,
) -> str:
    ACM_SEARCH_BASE = "https://dl.acm.org/action/doSearch"
    params: dict[str, object] = {
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
    groups: list[tuple[str, list[str]]],
    year_range: tuple[int, int] = (2022, 2025),
    exclude_filters: list[tuple[str, list[str]]] | None = None,  
) -> str:
    IEEE_SEARCH_BASE = "https://ieeexplore.ieee.org/search/searchresult.jsp"

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

def build_search_urls_for_sources(groups: list[tuple[str, list[str]]],
    year_range: tuple[int, int],
    exclude_filters: list[tuple[str, list[str]]] | None
) -> tuple[str, str]:
    start, end = year_range
    if exclude_filters:
        ieee_url = build_ieee_search_url(groups, year_range, exclude_filters)
        acm_url  = build_acm_search_url(groups, (start, 1), (end + 1, 1), exclude_filters) 
    else:
        ieee_url = build_ieee_search_url(groups, year_range)
        acm_url  = build_acm_search_url(groups, (start, 1), (end + 1, 1))         
    return ieee_url, acm_url

def split_urls_by_domain(urls: list[str]) -> tuple[list[str], list[str]]:
    ieee_list, acm_list = [], []
    for url in urls:
        if not url:
            continue
        netloc = urlparse(url).netloc.lower()
        if netloc.endswith("ieeexplore.ieee.org"):
            ieee_list.append(url)
        elif netloc.endswith("dl.acm.org"):
            acm_list.append(url)
    return ieee_list, acm_list

def fetch_and_save_results(source_name: str, source_handler, urls: list[str], tag: str, save_dir: str | os.PathLike) -> dict[str, str]: 
    tag_by_url = {url: f"{tag}_{i}" for i, url in enumerate(urls)}
    os.makedirs(os.path.join(save_dir, source_name.lower()), exist_ok=True)
    saved_files_by_path = {}
    
    for url in urls:
        try:
            research = source_handler.get_all_researches(url)
            if research:
                file_path = os.path.join(save_dir, source_name.lower(), f"{source_name.lower()}_research_{tag_by_url[url]}.pkl")
                with open(file_path, "wb") as file:
                    pickle.dump(research, file)      
                logger.debug(f"{source_name.upper()} research {tag_by_url[url]} completed and saved at {file_path}")
                saved_files_by_path[file_path] = url
            else:
                logger.error(f"There ins't any results for the url: {url}")
        except Exception:
            logger.error(f"Error while processing {source_name.upper()} research {tag_by_url[url]} from URL: {url}")
    return saved_files_by_path

def fetch_all_sources(urls: list[str], research_tag: str, save_dir: str | os.PathLike) -> tuple[dict[str, str], dict[str, str]]:
    ieee_urls, acm_urls = split_urls_by_domain(urls)
    
    with IEEESources() as ieee:
        saved_path_ieee = fetch_and_save_results("ieee", ieee, ieee_urls, research_tag, save_dir)
    with ACMSources() as acm:
        saved_path_acm = fetch_and_save_results("acm", acm, acm_urls, research_tag, save_dir)
    return saved_path_ieee, saved_path_acm

if __name__ == "__main__":
    import time
    year_range = (2022, 2025)
    
    exclude_noise = [
        ("Abstract", [
            "VLSI","circuit","PCB","hardware reverse engineering",
            "malware","virus","exploit","firmware","embedded systems","binary",
            "bytecode","opcode","binary instrumentation"
        ])
    ]

    start_time = time.time()

    year_range = (2020, 2025)  

    abstract_reverse_engineering = (
        "Abstract", [
            "reverse engineering","re-engineer","reengineer",
            "model recovery","design recovery","architecture recovery",
            "requirements recovery","software visualization","program comprehension"
        ]
    )
    
    abstract_oo = (
        "Abstract", [
            "object-oriented","object oriented","OO","OOP",
            "object-oriented software","class-based","inheritance","polymorphism"
        ]
    )
    
    abstract_code = (
        "Abstract", [
            "legacy system","code base","source code"
        ]
    )
    
    abstract_use_case_uml = (
        "Abstract", [
            "UML","UML reverse engineering","UML generation",
            "class diagram","sequence diagram","object diagram","state machine",
            "package diagram","component diagram","activity diagram",
            "interaction diagram","collaboration diagram",
            "use case","use-case","use case diagram","scenario"
        ]
    )
    
    abstract_static_analysis = (
        "Abstract", [
            "static analysis","source code analysis","program comprehension",
            "AST","call graph","dependency analysis","points-to analysis",
            "code inspection","software metrics","control flow analysis"
        ]
    )
    
    abstract_concept_location = (
        "Abstract", [
            "concept location","feature location","concern location",
            "information retrieval","IR","traceability",
            "requirements traceability","requirements extraction",
            "latent semantic indexing","LSI","topic modeling"
        ]
    )
    
    abstract_nlp = (
        "Abstract", [
            "natural language processing","NLP","information retrieval","concept location","LSI","latent semantic indexing"
        ]
    )
    
    groups_sets = {
    #   "reverse_oo_uml": [abstract_reverse_engineering, abstract_oo, abstract_use_case_uml], # 0/0
    #   
    #   "reverse_static_uml": [abstract_reverse_engineering, abstract_static_analysis, abstract_use_case_uml], # 7/2
    #   
    #   "concept_code_static_uml": [abstract_concept_location, abstract_code, abstract_static_analysis, abstract_use_case_uml], # 2/2
    #   
    #   "reverse_concept_uml": [abstract_reverse_engineering, abstract_concept_location, abstract_use_case_uml], # 0/1
    #   
    #   "reverse_concept_nlp": [abstract_reverse_engineering, abstract_concept_location, abstract_nlp], # 7/6
      
      "reverse_static_nlp": [abstract_reverse_engineering, abstract_static_analysis, abstract_nlp] # 8/7
    }

    count = 0 
    for name, groups in groups_sets.items():
        ieee, acm = build_search_urls_for_sources(groups, year_range, exclude_noise)
        #print(f"{count} - {name}:\n\nIEEE: {ieee}\n\nACM:  {acm}\n")
        #count += 1
        #print("-" * 80)
        urls = [ieee, acm]
        
        orchestrate_sources_ieee_acm = fetch_all_sources(urls, name, "papers")
    
    elapsed_time = time.time() - start_time
    logger.debug(f"Tempo total de execução: {elapsed_time:.2f} segundos")