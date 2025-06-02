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
    logger.debug(f"Section_key")
    TYPE_PATTERNS = [
        (0, re.compile(rf"^{section_key}$")),             
        (1, re.compile(rf"^\d+\s+{section_key}$")),       
        (2, re.compile(rf"^{section_key}\s+\d+$")),       
        (3, re.compile(rf"^\d+\.\s*{section_key}$")),      
        (4, re.compile(rf"^{section_key}\s+\d+\.$"))
    ]
    line = (left_text_raw + " " + right_text_raw).strip()

    for type_id, pattern in TYPE_PATTERNS:
        if pattern.fullmatch(line):
            return type_id
    return -1

def reviewed_completed_line(linha_completa: str, section: str, type_of_section: int) -> int:
    """
    Identifica se a linha completa bate com padrões válidos da segunda camada:
        1. SIGLA: section
        2. section :SIGLA
        3. SIGLA: section :SIGLA
        
    """
    section_escaped = re.escape(section)

    patterns = [
        re.compile(rf"^[A-Z]+:\s*{section_escaped}$"),                          # SIGLA: section
        re.compile(rf"^{section_escaped}\s*:\s*[A-Z]+$"),                      # section :SIGLA
        re.compile(rf"^[A-Z]+:\s*{section_escaped}\s*:\s*[A-Z]+$"),           # SIGLA: section :SIGLA
    ]

    linha = linha_completa.strip()

    for pattern in patterns:
        if pattern.fullmatch(linha):
            return 5
    return -1

def find_new_section(text: str, new_section_start: str, section_key: str) -> int:
    logger.debug(f"Procurando section: {new_section_start}")
    todas_ocorrencias = list(re.finditer(re.escape(new_section_start), text))
    
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
    logger.debug(f"ESSA EU MATEI DEMAIS!!")
    return valid_ocorrencias
           
if __name__ == "__main__":
    mock_req_doc_raw_path = os.path.join("tests", "mocks", "mock_0_req_doc_raw_text")
    
    filename_map = generate_filename_map(mock_req_doc_raw_path)
    logger.debug(f"Filename_map: {filename_map}")  