import pandas as pd
import nltk
import re
nltk.download("punkt")
from nltk.tokenize import sent_tokenize
from lisa.sub_lisa.logger import logger
from lisa.data_prepare import RequirementDocumentation, Section, Requirement, UserStory, UsageScenario
from typing import List
from lisa.sub_lisa.utils import find_new_section

def get_line_number(text: str, char_index: int) -> int:
    return text[:char_index].count('\n') + 1

class Chunker:
    def __init__(self, requirement_documentation_dataframe: pd.DataFrame, section_dataframe: pd.DataFrame):
        self.requirement_documentation_dataframe = requirement_documentation_dataframe
        self.section_dataframe = section_dataframe
        
    def find_section(self, document_text: str, section_text: str, section_key: str) -> int:
        """
        Find the section in the text document based on the section.
        
        Args:
            document_text (str): The text document to search in.
            section_text (str): The section text containing the section information.
        
        Returns:
            int: The starting index of the section line in the document.  
        """
        matches = find_new_section(document_text, section_text, section_key)
        
        n = len(matches)
        if n != 1:
            if n == 0:
                logger.error(f"Error dont matches: {section_text}")
            else:
                logger.error(f"Error are {n} matches: {section_text}")
            raise ValueError(f"Section founded error: {section_text}")
        
        return matches[0].start()
        
    def chunk_for_section(self):    
        chunks = []
        sections_len = 0 # retirar
        for i, row_document in self.requirement_documentation_dataframe.iterrows():
            logger.debug(f"Começando novo documento: {i}")
            id_document = row_document["id"]
            document_text = row_document["text"]    
            sections = self.section_dataframe[self.section_dataframe["req_doc_id"] == id_document] 
            if sections.empty:
                raise ValueError(f"req_doc_id not found: {id_document}")
            
            section_starts = []
            section_ids = []
            for _, section in sections.iterrows():
                sections_len+=1 # retirar
                logger.info(f"NEW SECTION!!!")
                start_section = self.find_section(document_text, document_text, str(section["id"].id))
                section_starts.append(start_section) # tenho que colocar o início da linha
                section_ids.append(section["id"])

            section_pairs =sorted(zip(section_ids, section_starts), key=lambda x: x[1])
            
            for idx in range(len(section_starts)):
                section_id, start = section_pairs[idx]
                end = section_pairs[idx + 1][1] if idx + 1 < len(section_pairs) else len(document_text)
                chunk_text = document_text[start:end]
                
                chunks.append({
                    "req_doc_id": id_document,
                    "section_id": section_id,
                    "text": chunk_text.strip()
                })
        
        return chunks
                
                
if __name__ == "__main__":
    from lisa.data_prepare import RequirementDocumentation, Section
    import os
    raw_text_doc_dir_path = os.path.join("data", "df", "df_req_docs.pkl")      
    doc_struct_dir_path = os.path.join("data", "df", "df_sections.pkl")   
    
    df_req_docs = pd.read_pickle(raw_text_doc_dir_path)
    df_sections = pd.read_pickle(doc_struct_dir_path)
    chunker = Chunker(df_req_docs, df_sections)
    chunker.chunk_for_section()        