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

def is_matching_section(line: str, section_text, section_id) -> bool:
    """
    Verifica se a linha é (ou contém) a seção "2.3 Caso de teste singular"
    considerando variações de ordem e pontuação.
    """
    line = line.strip().lower()

    pattern_text = rf"{section_text}"
    section_id = "\b" + section_id.replace(".", "\.") + "\b\.?"
    pattern_num = rf"{section_id}"

    patterns = [
        rf"^{pattern_num}\s+{pattern_text}$",              # "2.3 Caso de teste singular"
        rf"^{pattern_num}\.\s*{pattern_text}$",            # "2.3. Caso de teste singular"
        rf"^{pattern_text}\s+{pattern_num}$",              # "Caso de teste singular 2.3"
        rf"^{pattern_text}\s+{pattern_num}\.$",            # "Caso de teste singular 2.3."
        rf"^{pattern_text}$",                              # "Caso de teste singular"
        rf"{pattern_num}\s+{pattern_text}",                # Em uma linha com frase maior
        rf"{pattern_text}\s+{pattern_num}",                # Em uma linha com frase maior
    ]

    return any(re.search(p, line) for p in patterns)

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
    rest_line_parts = linha_completa.split(section)
    
    rest_line_parts = [part.strip() for part in rest_line_parts if part.strip()]
    rest_line = " ".join(rest_line_parts)
    if len(rest_line.split(" ")) == 1:
        return 5
    else:   
        return -1

def find_new_section(text: str, new_section_start: str, section_key: str) -> int:
    logger.debug(f"Procurando section: {new_section_start}")
    todas_ocorrencias = list(re.finditer(re.escape(new_section_start), text))
    
    pattern = re.compile()
    valid_ocorrencias = []
    
    logger.debug(f"Quantidade de ocorrencias encontradas: {len(todas_ocorrencias)}")
    for i, ocorrencia in enumerate(todas_ocorrencias):
        linha_inicio = text.rfind('\n', 0, ocorrencia.start()) + 1
        linha_fim = text.find('\n', ocorrencia.end())
        linha_completa = text[linha_inicio:linha_fim]
        logger.debug(f"Linha completa onde há ocorrencia: {linha_completa}")
        
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
    logger.debug(f"Número ideal de ocorrências encontradas: 1 e temos {len(valid_ocorrencias)}")
    logger.debug(f"FOI!!")
    return valid_ocorrencias
           
if __name__ == "__main__":
    mock_req_doc_raw_path = os.path.join("tests", "mocks", "mock_0_req_doc_raw_text")
    
    filename_map = generate_filename_map(mock_req_doc_raw_path)
    logger.debug(f"Filename_map: {filename_map}")  