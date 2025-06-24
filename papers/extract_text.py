import PyPDF2 as pp
import os

def extract_text_from_a_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        pdf_reader = pp.PdfReader(file)
        text = ""

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            text += page_text + "\n"
    return text

def save_string_in_txt(file_name, string_text):
    with open(file_name, "w") as file:
        file.write(string_text)

multilingual_source_code_analysis = extract_text_from_a_pdf(os.path.join("papers", "Multilingual_Source_Code_Analysis_A_Systematic_Literature_Review.pdf"))

save_string_in_txt(os.path.join("papers", "Multilingual_Source_Code_Analysis_A_Systematic_Literature_Review.txt"), multilingual_source_code_analysis)