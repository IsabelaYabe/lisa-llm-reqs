from lisa.sub_lisa.logger import logger
from webscraping.web_driver_config import *
import pickle
import os
from urllib.parse import urlparse
from urllib.parse import urlencode, quote, quote_plus

def build_acm_url(
    conditions: list[tuple[str, list[str]]],
    after: tuple[int, int] = (2022, 1),
    before: tuple[int, int] = (2026, 1),
    exclude: list[tuple[str, list[str]]] | None = None,
) -> str:
    base = "https://dl.acm.org/action/doSearch"
    params: dict[str, object] = {
        "fillQuickSearch": "false",
        "target": "advanced",
        "expand": "dl",
        "AfterMonth": after[1],
        "AfterYear": after[0],
        "BeforeMonth": before[1],
        "BeforeYear": before[0],
    }

    i = 1
    for field, terms in conditions:
        params[f"field{i}"] = field
        params[f"text{i}"]  = "(" + " OR ".join(f'"{t}"' for t in terms) + ")"
        i += 1

    if exclude:
        for field, terms in exclude:
            params[f"field{i}"] = field
            params[f"text{i}"]  = "NOT (" + " OR ".join(f'"{t}"' for t in terms) + ")"
            i += 1

    return f"{base}?{urlencode(params, quote_via=quote_plus)}"

def build_ieee_url(
    groups: list[tuple[str, list[str]]],
    year_range: tuple[int, int] = (2022, 2025),
    exclude: list[tuple[str, list[str]]] | None = None,  
) -> str:
    base = "https://ieeexplore.ieee.org/search/searchresult.jsp"

    include_parts = [
        "(" + " OR ".join(f'"{field}":"{t}"' for t in terms) + ")"
        for field, terms in groups
    ]

    if exclude:
        include_parts += [
            "NOT (" + " OR ".join(f'"{field}":"{t}"' for t in terms) + ")"
            for field, terms in exclude
        ]

    query_text = " AND ".join(include_parts)

    params = {
        "action": "search",
        "newsearch": "true",
        "matchBoolean": "true",
        "queryText": query_text,
        "ranges": f"{year_range[0]}_{year_range[1]}_Year",
    }
    return f"{base}?{urlencode(params, quote_via=quote)}"

def build_ieee_acm_urls(groups: list[tuple[str, list[str]]],
    year_range: tuple[int, int],
    exclude: list[tuple[int, list[str]]] | None
) -> tuple[str, str]:
    if exclude:
        ieee_url, acm_url = build_ieee_url(groups, year_range, exclude), build_acm_url(groups, (year_range[0], 1), (year_range[0]+1, 1), exclude)
    else:    
        ieee_url, acm_url = build_ieee_url(groups, year_range), build_acm_url(groups, (year_range[0], 1), (year_range[0]+1, 1))
    return ieee_url, acm_url

def separete_ieee_and_acm_urls(urls: list[str]) -> tuple[list[str], list[str]]:
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

def save_source_results(source_name: str, source_handler, urls: list[str], tag: str, save_dir: str | os.PathLike) -> dict[str, str]: 
    tag_by_url = {url: f"{tag}_{i}" for i, url in enumerate(urls)}
    os.makedirs(os.path.join(save_dir, source_name.lower()), exist_ok=True)
    saved_paths = {}
    
    for url in urls:
        try:
            research = source_handler.get_all_researches(url)
            if research:
                file_path = os.path.join(save_dir, source_name.lower(), f"{source_name.lower()}_research_{tag_by_url[url]}.pkl")
                with open(file_path, "wb") as file:
                    pickle.dump(research, file)      
                logger.debug(f"{source_name.upper()} research {tag_by_url[url]} completed and saved at {file_path}")
                saved_paths[file_path] = url
            else:
                logger.error(f"There ins't any results for the url: {url}")
        except Exception:
            logger.error(f"Error while processing {source_name.upper()} research {tag_by_url[url]} from URL: {url}")
    return saved_paths

def get_sources(urls: list[str], research_tag: str, save_dir: str | os.PathLike) -> tuple[dict[str, str], dict[str, str]]:
    ieee_urls, acm_urls = separete_ieee_and_acm_urls(urls)
    
    with IEEESources() as ieee:
        saved_path_ieee = save_source_results("ieee", ieee, ieee_urls, research_tag, save_dir)
    with ACMSources() as acm:
        saved_path_acm = save_source_results("acm", acm, acm_urls, research_tag, save_dir)
    return saved_path_ieee, saved_path_acm

if __name__ == "__main__":
    import time
    start_time = time.time()
    
    url_ieee_0, url_acm_0 = build_ieee_acm_urls([
        ("Abstract", ["reverse engineering", "re-engineer", "reengineer"]),
        ("Abstract", ["object-oriented", "object oriented"]),
    ], year_range=(2022, 2025), exclude = None)
     
    url_ieee_1, url_acm_1 = build_ieee_acm_urls([
        ("Abstract", ["reverse engineering", "re-engineer", "reengineer"]),
        ("Abstract", ["functional requirements", "use case", "UML"])
    ], year_range=(2022, 2025), exclude = None)
    
    url_ieee_2, url_acm_2 = build_ieee_acm_urls([
        ("Abstract", ["reverse engineering", "re-engineer", "reengineer"]),
        ("Abstract", ["source code"]),
    ], year_range=(2022, 2025), exclude = None)
    
    url_ieee_3, url_acm_3 = build_ieee_acm_urls([
        ("Abstract", ["source code analysis"]),
        ("Abstract", ["software"]),
        ("Abstract", ["object-oriented", "object oriented"]),
    ], year_range=(2022, 2025), exclude = None)

    url_ieee_0, url_acm_0 = build_ieee_acm_urls([
        ("Abstract", ["reverse engineering", "re-engineer", "reengineer"]),
        ("Abstract", ["software"]),
        ("Abstract", ["object-oriented", "object oriented"]),
    ], year_range=(2022, 2025), exclude = None)    
    
    #url_ieee_1 = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22Abstract%22:source%20code%20analysis)%20AND%20(%22Abstract%22:language%20models)%20AND%20(%22Abstract%22:reverse%20engineering)" 
    #url_acm_1 = "https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=dl&field1=Abstract&text1=+source+code+analysis&field2=AllField&text2=language+models&field3=Abstract&text3=reverse+engineering&AfterMonth=1&AfterYear=2022&BeforeMonth=6&BeforeYear=2025"
    
    #ieee_url_1 = "https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&matchBoolean=true&newsearch=true&queryText=((%22source%20code%20analysis%22)%20AND%20((%22reverse%20engineering%22)%20OR%20(%22re-engineer%22)%20OR%20(%22reengineer%22))%20AND%20((%22object-oriented%22)%20OR%20(%22object%20oriented%22))%20AND%20((%22functional%20requirements%22)%20OR%20(%22use%20case%22)%20OR%20(%22UML%22)))"
    #acm_url_1 = "https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=dl&field1=Fulltext&text1=%28%22source+code+analysis%22%29+AND+%28%28%22reverse+engineering%22%29+OR+%28%22re-engineer%22%29+OR+%28%22reengineer%22%29%29+AND+%28%28%22object-oriented%22%29+OR+%28%22object+oriented%22%29%29+AND+%28%28%22functional+requirements%22%29+OR+%28%22use+case%22%29+OR+%28%22UML%22%29%29+AND+%28%22LLM%22%29+AND+%28%22BERT%22%29+AND+%28%22use+case+diagram%22%29"
    
    urls = [url_ieee_0, url_acm_0]
    #os.makedirs("z_teste", exist_ok=True)
    get_sources_ieee_acm = get_sources(urls, "teste", "yy_teste")
    
    elapsed_time = time.time() - start_time
    logger.debug(f"Tempo total de execução: {elapsed_time:.2f} segundos")