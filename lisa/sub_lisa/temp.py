import os
import re
from lisa.sub_lisa.logger import logger

def generate_filename_map(directory):
    """
    Generates two mappings of filenames in a directory.

    Args:
        directory (str): Path to the directory.

    Returns:
        tuple[dict, dict]: 
            - filenames_map: keys = names without extensions, values = index
            - map_filenames: keys = index, values = names without extensions
    """
    filenames_map = {}
    map_filenames = {}
    
    files = sorted(os.listdir(directory))
    for i, file in enumerate(files):
        filename = os.path.splitext(file)[0]
        filenames_map[filename] = str(i)
        #map_filenames[str(i)] = filename
        
    return filenames_map 
    
def find_new_section(text: str, new_section_start: str, section_key: str) -> int: 
    #logger.debug(f"find_new_section: {new_section_start}")
    #logger.debug(f"section_key: {section_key}") 
    todas_ocorrencias = list(re.finditer(re.escape(new_section_start), text))
    
    valid_ocorrencias = []
    for i, ocorrencia in enumerate(todas_ocorrencias):
        #logger.debug(";|;|"*60)
        #logger.debug("Analisando ocorrencia")
        #logger.debug(f"Ocorrencia {i}: {ocorrencia}")
        text_left = text[:ocorrencia.start()]
        text_right = text[ocorrencia.end():]
        
        text_left = text_left[text_left.rfind("\n"):]
        text_right = text_right[:text_right.find("\n")]
        #logger.debug(f"Ocorrencia {i}: {text_left} | {text_right}")
        
        left_ok = True
        right_ok = True
        text_left_raw = text_left.strip()
        text_right_raw = text_right.strip()
        if text_left_raw != section_key and text_left_raw != "":
            #logger.debug(";=;="*60)
            #logger.debug("Analisando a esquerda")
            #logger.debug(f"Ocorrencia {i}: {text_left}")
            #logger.debug(f"text_left_raw: {text_left_raw} | section_key: {section_key}")
            left_ok = False
        if text_right_raw != section_key and text_right_raw != "":
            #logger.debug(";=;="*60)
            #logger.debug("Analisando a direita")
            #logger.debug(f"Ocorrencia {i}: {text_right}")
            #logger.debug(f"text_right_raw: {text_right_raw} | section_key: {section_key}")
            right_ok = False
        #logger.debug(f"left_ok: {left_ok} | right_ok: {right_ok}")
        #logger.debug("Ocorrencia válida esperada: left_ok: True and right_ok: True")
        if left_ok and right_ok: 
            #logger.debug(";=;="*60)
            #logger.debug("Ocorrencia válida")
            #logger.debug(f"Ocorrencia {i}: {text_left} | {text_right}")
            valid_ocorrencias.append(ocorrencia)
    #logger.debug(";|;|"*60)
    #logger.debug(f"Ocorrencias válidas: {len(valid_ocorrencias)}")
    #logger.debug(f"Ocorrencias válidas: {valid_ocorrencias}")
    if len(valid_ocorrencias) == 0:
        logger.warning(f"Warning finded in: {new_section_start}")
        logger.error(f"Error dont matches: {new_section_start}")
        raise ValueError(f"Section founded error: {new_section_start}")
    if len(valid_ocorrencias) > 1:
        logger.warning(f"Warning finded in: {new_section_start}")
        logger.error(f"Error are {len(valid_ocorrencias)} matches: {new_section_start}")
        raise ValueError(f"Section founded error: {new_section_start}")
    if len(valid_ocorrencias) == 1:
        return valid_ocorrencias
           
if __name__ == "__main__":
    #mock_req_doc_raw_path = os.path.join("tests", "mocks", "mock_0_req_doc_raw_text")
    
    #filename_map = generate_filename_map(mock_req_doc_raw_path)
    ##logger.debug(f"Filename_map: {filename_map}")  
    with open(os.path.join("data", "ReqList_ReqNet_ReqSim", "0.1 Raw Text", "0000 - gamma j.txt"), "r") as file:
        text = file.read()          
        
    word_to_find = "Overall Description"
    key =  "2."
    ocorrencias_validas = find_new_section(text, word_to_find, key)
    logger.debug(f"\n[RESULTADO FINAL] Ocorrências válidas para '{word_to_find}': {len(ocorrencias_validas)}")
    for idx, o in enumerate(ocorrencias_validas):
        trecho = text[o.start():text.find("\n", o.end())]
        logger.debug(f"  - {idx + 1}) '{trecho.strip()}' (índice {o.start()})")