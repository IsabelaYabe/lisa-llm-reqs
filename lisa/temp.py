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

def type_of_section(section_key: str, left_text_raw: str, right_text_raw: str):
    """
    Há apenas 5 tipos de linha completa de seção válidas para essa primeira camada:
        "NewSection" := type 0
        "2 NewSection" := type 1
        "NewSection 2" := type 2
        "2. NewSection" := type 3
        "NewSection 2." := type 4
        
    Desses 5 tipos há 3 typos de section:
        just_section_name := [0]
        id_section := [1,2]
        id_dot_section := [3,4] 
    """
    logger.debug(f"left_text_raw: {left_text_raw} | right_text_raw: {right_text_raw}")
    logger.debug(f"Section_key: {section_key}")
    if left_text_raw == "" and right_text_raw == "":
        i = 0
    elif left_text_raw == section_key and right_text_raw == "":
        i = 1
    elif left_text_raw == "" and right_text_raw == section_key:
        i = 2
    elif left_text_raw == f"{section_key}." and right_text_raw == "":
        i = 3
    elif left_text_raw == "" and right_text_raw == f"{section_key}.":
        i = 4
    else:
        i = -1
    logger.debug(f"tipo de ocorrencia: {i}")
    return i

def reviewed_completed_line(linha_completa: str, section: str, type_of_section: int):
    """
    Há apenas 2 tipo de linha completa de seção válidas para essa awgunda camada:
        SIGLA: section_name
        section_name :SIGLA
        
    Desses 2 tipos há 1 typo de section:
        just_section_name := [0]
        id_section := [1,2]
        id_dot_section := [3,4]
        sigla_setion := [5] 
    
    """
    logger.debug(f"Completed line before rest_line: {linha_completa}")
    rest_line_parts = linha_completa.split(section)
    n_parts = len(rest_line_parts)
    
    if n_parts != 2:
        logger.warning(f"A linha não foi dividida em duas partes como esperado. n_parts: {n_parts}")
    
    rest_line_parts = [part.strip() for part in rest_line_parts if part.strip()]
    rest_line = " ".join(rest_line_parts)
    logger.debug(f"Completed line after rest_line: {linha_completa}")
    logger.debug(f"rest_line: {rest_line}")
    if len(rest_line.split(" ")) == 1:
        return 5
    

def find_new_section(text: str, new_section_start: str, section_key: str) -> int:
    todas_ocorrencias = list(re.finditer(re.escape(new_section_start), text))
    valid_ocorrencias = []
    retirar_quebra_de_linha = 1    
    
    for i, ocorrencia in enumerate(todas_ocorrencias):
        
        linha_inicio = text.rfind('\n', 0, ocorrencia.start()) + retirar_quebra_de_linha
        
        linha_fim = text.find('\n', ocorrencia.end())
        linha_completa = text[linha_inicio:linha_fim]
        
        text_left = text[:ocorrencia.start()]
        text_right = text[ocorrencia.end():]
        
        text_left = text_left[text_left.rfind("\n"):]
        text_right = text_right[:text_right.find("\n")]

        text_left_raw = text_left.strip()
        text_right_raw = text_right.strip()

        type_of_section_num = type_of_section(section_key, text_left_raw,  text_right_raw)
        
        if type_of_section_num == -1:
            reviewed_completed_line(linha_completa, new_section_start, type_of_section_num)
        
        valid_ocorrencia = False
        if type_of_section_num == 0:
            valid_ocorrencia = True
            num_ocorrencia_max = 1
        if type_of_section_num in [1,2]:
            valid_ocorrencia = True
            num_ocorrencia_max = 0
        if type_of_section_num in [3,4]:
            valid_ocorrencia = True
            num_ocorrencia_max = -1              
        
        if valid_ocorrencia:
            if num_ocorrencia_max == 1:
                valid_ocorrencias.append(ocorrencia)
                logger.debug(f"Uma ocorrencia foi adicionada: {linha_completa}; caso 0")
            elif num_ocorrencia_max == 0:
                if section_key in linha_completa:
                    valid_ocorrencias.append(ocorrencia)
                    logger.debug(f"Uma ocorrencia foi adicionada: {linha_completa}; caso [1,2]")
            elif num_ocorrencia_max == -1:
                if f"{section_key}." in linha_completa:
                    valid_ocorrencias.append(ocorrencia)
                    logger.debug(f"Uma ocorrencia foi adicionada: {linha_completa}; caso [3,4]")
        else:
            logger.warning(f"Primeira avaliação: nenhuma ocorrencia foi inserida com type_of_section")
            
    if len(valid_ocorrencias)==0:
        logger.error(f" Não foram encontradas ocorrências válidas para '{new_section_start}'")
        logger.debug(f"type_of_section_num: {type_of_section_num}")
        logger.debug(f"linha_completa: {linha_completa}")
        type_of_section_num=reviewed_completed_line(linha_completa, new_section_start, type_of_section_num)
        logger.debug(f"type_of_section_num: {type_of_section_num}")
        if type_of_section_num == 5:
            valid_ocorrencias.append(ocorrencia)
            logger.debug(f"Uma ocorrencia foi adicionada: {linha_completa}; caso 5")
        else:
            logger.warning(f"Segunda avaliação: nenhuma ocorrencia foi inserida com reviewed_completed_line")
            raise ValueError
        
    if len(valid_ocorrencias)>1:
        logger.error(f"Mais de uma ocorrência válida foi encontrada para '{new_section_start}', foram encontradas {len(valid_ocorrencias)}.")
    logger.debug(f"Ocorrencias válidas: {valid_ocorrencias}")
    return valid_ocorrencias


           
if __name__ == "__main__":
    mock_req_doc_raw_path = os.path.join("tests", "mocks", "mock_0_req_doc_raw_text")
    
    filename_map = generate_filename_map(mock_req_doc_raw_path)
    logger.debug(f"Filename_map: {filename_map}")  