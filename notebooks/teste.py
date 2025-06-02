import sys
import os
import pandas as pd

# Adiciona o diretório pai ao sys.path para importações
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
from lisa.sub_lisa.logger import logger

# Caminhos dos arquivos
req_user_stories_path = os.path.join("data", "df", "df_user_stories.pkl")
print("Procurando arquivo em:", os.path.abspath(req_user_stories_path))
if not os.path.exists(req_user_stories_path):
    print("Arquivo não encontrado:", req_user_stories_path)
    raise FileNotFoundError(f"Arquivo não encontrado: {req_user_stories_path}")
else:
    print("Arquivo encontrado:", req_user_stories_path)
    print("Caminho absoluto:", os.path.abspath(req_user_stories_path))
req_docs_path = os.path.join("data", "df", "df_req_docs.pkl")
req_list_path = os.path.join("data", "df", "df_requirements.pkl")
sections_path = os.path.join("data", "df", "df_sections.pkl")

# Carrega os DataFrames
df_user_stories = pd.read_pickle(req_user_stories_path)
df_req_docs = pd.read_pickle(req_docs_path)
df_requirements = pd.read_pickle(req_list_path)
df_metadatas = pd.read_pickle(sections_path)

# Função para criar um arquivo de teste com o texto do primeiro documento
def create_test_file():
    try:
        with open("test.txt", "w", encoding="utf-8") as f:
            f.write(df_req_docs.iloc[0]["text"])
        logger.info("Arquivo de teste criado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao criar o arquivo de teste: {e}")

def get_full_path(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        current_dir = os.getcwd()
    return os.path.join(current_dir, file_name)

if __name__ == "__main__":
    caminho_absoluto_diretorio = os.path.abspath(os.path.dirname(__file__))
    caminho_absoluto_df_user_stories = os.path.abspath(req_user_stories_path)
    print("Caminho absoluto do diretório:", caminho_absoluto_diretorio)
    print("Caminho absoluto do arquivo df_user_stories:", caminho_absoluto_df_user_stories)
    create_test_file()
    file_name = "test.txt"
    full_path = get_full_path(file_name)
    print("O caminho completo do arquivo é:", full_path)