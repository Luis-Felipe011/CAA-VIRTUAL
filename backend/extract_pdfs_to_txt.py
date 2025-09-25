# Script para extrair texto de todos os PDFs em uma pasta e salvar como .txt
import os
from pathlib import Path
from PyPDF2 import PdfReader

PDF_DIR = 'data/pdfs'  # ajuste para o caminho dos seus PDFs
TXT_DIR = 'data/docs'  # onde salvar os .txt extraídos
os.makedirs(TXT_DIR, exist_ok=True)

for pdf_file in Path(PDF_DIR).rglob('*.pdf'):
    try:
        reader = PdfReader(str(pdf_file))
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
        txt_path = Path(TXT_DIR) / (pdf_file.stem + '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Extraído: {pdf_file} -> {txt_path}')
    except Exception as e:
        print(f'Erro ao extrair {pdf_file}: {e}')
