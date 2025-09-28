import time
from logger import logger

from papers_lab.sources.url_builder import build_search_urls_for_sources
from papers_lab.sources.orchestrator import SourcesOrchestrator
from papers_lab.io.repo import PapersRepo

# (opcional) se quiser forçar headless nos providers usados pelo orchestrator,
# ajuste no orchestrator para passar **cfg (headless=True) na construção
# ou rode com variável de ambiente CHROME_HEADLESS=1 e leia isso no __init__.

year_range = (2020, 2025)

exclude_noise = [
    ("Abstract", [
        "VLSI","circuit","PCB","hardware reverse engineering",
        "malware","virus","exploit","firmware","embedded systems","binary",
        "bytecode","opcode","binary instrumentation"
    ])
]

abstract_reverse_engineering = (
    "Abstract", [
        "reverse engineering","re-engineer","reengineer",
        "model recovery","design recovery","architecture recovery",
        "requirements recovery","software visualization","program comprehension"
    ]
)
abstract_oo = ("Abstract", ["object-oriented","object oriented","OO","OOP","object-oriented software","class-based","inheritance","polymorphism"])
abstract_code = ("Abstract", ["legacy system","code base","source code"])
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
#   "reverse_oo_uml": [abstract_reverse_engineering, abstract_oo, abstract_use_case_uml],
#   "reverse_static_uml": [abstract_reverse_engineering, abstract_static_analysis, abstract_use_case_uml],
    "concept_code_static_uml": [abstract_concept_location, abstract_code, abstract_static_analysis, abstract_use_case_uml],
#   "reverse_concept_uml": [abstract_reverse_engineering, abstract_concept_location, abstract_use_case_uml],
#   "reverse_concept_nlp": [abstract_reverse_engineering, abstract_concept_location, abstract_nlp],
   "reverse_static_nlp": [abstract_reverse_engineering, abstract_static_analysis, abstract_nlp],
}

def main():
    start_time = time.time()
    repo = PapersRepo()
    orch = SourcesOrchestrator(repo) 

    for name, groups in groups_sets.items():
        ieee_url, acm_url = build_search_urls_for_sources(groups, year_range, exclude_noise)
        logger.debug(f"[{name}] IEEE URL: {ieee_url}")
        logger.debug(f"[{name}] ACM URL: {acm_url}")
        # urls = [ieee_url, acm_url]
        urls = [ieee_url]
        # urls = [acm_url]

        logger.debug(f"[{name}] Starting search…")
        saved_ieee, saved_acm = orch.fetch_all(urls, research_tag=name, save_dir="papers_test")

        logger.debug(f"[{name}] IEEE saved: {len(saved_ieee)} | ACM saved: {len(saved_acm)}")

    elapsed = time.time() - start_time
    logger.debug(f"Total execution time: {elapsed:.2f} s")

if __name__ == "__main__":
    main()