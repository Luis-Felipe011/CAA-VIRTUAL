# --- Analisador de Documentos (Módulo Otimizado para Apresentação) ---

import warnings
warnings.filterwarnings("ignore")

import cv2
from PIL import Image
import os
import pandas as pd
import numpy as np
from transformers import DonutProcessor, VisionEncoderDecoderModel
import torch
import fitz
import json
import psycopg2
import shutil
import logging
import re
from datetime import datetime, timedelta
import easyocr
from unidecode import unidecode
import signal
from contextlib import contextmanager
# --- MUDANÇA AQUI: Trocado Process por Thread ---
from concurrent.futures import ThreadPoolExecutor, as_completed 

# Configuração básica do logging para ver as mensagens no terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Modelos Globais (Lazy Loading) ---
model_ai = None
ocr_reader = None
processor = None
device = None

def init_models():
    """
    Inicializa os modelos de IA apenas na primeira chamada.
    AGORA É CHAMADO APENAS UMA VEZ, NO PROCESSO PRINCIPAL.
    """
    global model_ai, ocr_reader, processor, device
    if model_ai is not None:
        return

    # --- MUDANÇA AQUI: Removido o f"[Processo {os.getpid()}]" para clareza ---
    logging.info(f"Inicializando Modelos de IA (pode demorar)...")
    try:
        processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
        model_ai = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_ai.to(device)
        logging.info(f"Modelo de Extração (Donut) inicializado em '{device}'.")
        ocr_reader = easyocr.Reader(['pt'], gpu=False)
        logging.info(f"Modelo de Classificação (EasyOCR) inicializado.")
    except Exception as e:
        logging.error(f"AVISO: Não foi possível carregar um dos modelos de IA. Erro: {e}")

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config(config_path=None):
    """Carrega o ficheiro de configuração de forma robusta."""
    if config_path is None:
        config_path = os.path.join(_CURRENT_DIR, "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"ERRO CRÍTICO ao carregar configuração '{config_path}': {e}")
        return None

def ask_ai(image_path, question):
    if not model_ai: return ""
    try:
        image = Image.open(image_path).convert("RGB")
        pixel_values = processor(image, return_tensors="pt").pixel_values
        task_prompt = f"<s_docvqa><s_question>{question}</s_question><s_answer>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids
        outputs = model_ai.generate(
            pixel_values.to(device),
            decoder_input_ids=decoder_input_ids.to(device),
            max_length=model_ai.decoder.config.max_position_embeddings,
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            use_cache=True, bad_words_ids=[[processor.tokenizer.unk_token_id]], return_dict_in_generate=True
        )
        sequence = processor.batch_decode(outputs.sequences)[0]
        sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        return processor.token2json(sequence).get('answer', '')
    except Exception as e:
        logging.error(f"Erro ao perguntar à IA para a imagem {os.path.basename(image_path)}: {e}")
        return ""

def classify_document_with_ocr(image_path, config):
    """
    Classifica o documento usando EasyOCR, mas APENAS no topo da imagem (cabeçalho).
    """
    if not ocr_reader: 
        logging.error("EasyOCR (ocr_reader) não foi inicializado.")
        return "Erro OCR"
        
    try:
        img = cv2.imread(image_path)
        if img is None:
             logging.error(f"Não foi possível ler a imagem para OCR: {image_path}")
             return "Erro Leitura Imagem"
        
        height = img.shape[0]
        crop_height = int(height * 0.40) # Corta em 40% do topo
        
        if crop_height < 50: 
            header_crop = img
        else:
            header_crop = img[0:crop_height, :] 

        gray_crop = cv2.cvtColor(header_crop, cv2.COLOR_BGR2GRAY)
        
        logging.info(f"Executando OCR otimizado (no cabeçalho) de: {os.path.basename(image_path)}")
        text = ' '.join(ocr_reader.readtext(gray_crop, detail=0, paragraph=False)).lower() 
        
        classification_rules = config.get("classification_rules", {})
        for category, keywords in classification_rules.items():
            if any(keyword in text for keyword in keywords):
                logging.info(f"Documento '{os.path.basename(image_path)}' classificado como: {category}")
                return category
                
        logging.warning(f"Documento '{os.path.basename(image_path)}' não classificado, retornando 'Outros'. Texto OCR: '{text[:100]}...'")
        return "Outros"
        
    except Exception as e:
        logging.error(f"Erro durante a classificação com OCR Otimizado para '{os.path.basename(image_path)}': {e}")
        return "Erro OCR"

def extract_data(image_path, category, config):
    extraction_profiles = config.get("extraction_profiles", {})
    profile = extraction_profiles.get(category)
    if not profile: return None
    extracted_data = {}
    logging.info(f"Iniciando extração para categoria '{category}' no ficheiro '{os.path.basename(image_path)}'...")
    for field, questions in profile.items():
        answer = "" 
        for i, question in enumerate(questions): 
            logging.info(f"Tentando pergunta {i+1}/{len(questions)} para '{field}': '{question}'")
            answer = ask_ai(image_path, question)
            if answer and isinstance(answer, str) and "n/a" not in answer.lower() and len(answer.strip()) > 1: 
                extracted_data[field] = answer.strip() 
                logging.info(f"==> Resposta encontrada para '{field}': '{answer.strip()}'")
                break 
        if field not in extracted_data: 
             logging.warning(f"### Nenhuma resposta válida encontrada para o campo '{field}' na categoria '{category}'.")
    
    if not extracted_data:
        logging.warning(f"Nenhum dado extraído para a categoria '{category}' no ficheiro '{os.path.basename(image_path)}'.")
        return None 

    return extracted_data

def prepare_batch_files(batch_folder, config):
    max_pages = config["processing_settings"]["pdf_max_pages_to_process"]
    batch_data = {'files': [], 'original_files': set()}
    try:
        all_files = os.listdir(batch_folder)
    except FileNotFoundError:
        logging.error(f"A pasta de entrada especificada não foi encontrada: {batch_folder}")
        return batch_data 

    for filename in all_files:
        path = os.path.join(batch_folder, filename)
        if not os.path.isfile(path): 
             continue
        
        batch_data['original_files'].add(path)
        
        supported_image_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        if path.lower().endswith(supported_image_formats):
             batch_data['files'].append(path)
        elif path.lower().endswith('.pdf'):
            try:
                doc = fitz.open(path)
                num_pages_to_process = min(max_pages, doc.page_count)
                logging.info(f"Convertendo {num_pages_to_process} página(s) do PDF '{filename}'...")
                for i in range(num_pages_to_process):
                    page = doc.load_page(i)
                    pix = page.get_pixmap()
                    image_path = os.path.join(batch_folder, f"{os.path.splitext(filename)[0]}_pagina_{i+1}.png") 
                    pix.save(image_path)
                    batch_data['files'].append(image_path)
                doc.close()
            except Exception as e:
                logging.error(f"Erro ao converter PDF '{filename}': {e}")
                batch_data['files'].append({'path': path, 'error': str(e)})
        else:
             logging.warning(f"Ficheiro ignorado (formato não suportado): {filename}")
             
    return batch_data

def assess_quality(image_path, config):
    blur_threshold = config["processing_settings"]["quality_blur_threshold"]
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None: return "Reprovado (Erro ao ler imagem)"
        variance = cv2.Laplacian(img, cv2.CV_64F).var()
        status = "Aprovado" if variance >= blur_threshold else f"Reprovado - Baixa nitidez ({variance:.2f})"
        logging.info(f"Avaliação de qualidade para '{os.path.basename(image_path)}': {status}")
        return status
    except Exception as e:
        logging.error(f"Erro na avaliação de qualidade para '{os.path.basename(image_path)}': {e}")
        return f"Reprovado (Erro: {e})"

def generate_batch_summary(batch_id, batch_results, config):
    summary = {}
    required_docs = set(config.get("processing_settings", {}).get("required_docs_checklist", []))
    found_docs_categories = {result.get('categoria', 'N/A') for result in batch_results}
    
    missing_docs = list(required_docs - found_docs_categories)
    summary['alerta_checklist'] = f"Atenção: Documentos essenciais ausentes: {missing_docs}" if missing_docs else "OK"
    
    reprovados = [res['arquivo'] for res in batch_results if "Reprovado" in res.get('qualidade', '')]
    summary['resumo_qualidade'] = {'total_processado': len(batch_results), 'reprovados': len(reprovados), 'lista_reprovados': reprovados}
    
    names = set()
    for res in batch_results:
         dados = res.get("dados_extraidos")
         if isinstance(dados, dict): 
             for key, val in dados.items():
                 if "nome" in key.lower() and isinstance(val, str) and val:
                     names.add(val.strip().title())

    alerta_consistencia = "N/A (Nenhum nome extraído)" 
    if len(names) > 1:
        alerta_consistencia = f"Divergência de nomes nos documentos: {list(names)}"
    elif len(names) == 1:
        extracted_name = unidecode(list(names)[0].lower())
        clean_batch_id_parts = [part for part in unidecode(batch_id.lower()).replace('_', ' ').replace('-', ' ').split() if not part.isdigit() and len(part) > 1]
        clean_batch_id = " ".join(clean_batch_id_parts)

        nome_encontrado_no_lote = False
        if clean_batch_id: 
            for part_nome in extracted_name.split():
                 if len(part_nome) > 2 and part_nome in clean_batch_id:
                     nome_encontrado_no_lote = True
                     break
        
        if nome_encontrado_no_lote:
             alerta_consistencia = f"OK (Nome '{list(names)[0]}' consistente com o lote)"
        elif clean_batch_id: 
             alerta_consistencia = f"Alerta: Nome '{list(names)[0]}' pode não corresponder ao lote '{batch_id}'."
        else: 
             alerta_consistencia = f"OK (Nome '{list(names)[0]}' extraído, sem nome de referência no lote)"

    summary['alerta_consistencia'] = alerta_consistencia
    return summary

def manage_db_connection(config, batch_id, batch_summary, document_results, candidato_id=None):
    """
    (Versão Completa) Conecta-se ao banco de dados e salva os resultados.
    Agora inclui o candidato_id.
    """
    try:
        conn = psycopg2.connect(**config["db_credentials"])
        cur = conn.cursor()
        summary_json = json.dumps(batch_summary, ensure_ascii=False)
        cur.execute("SELECT id FROM lotes WHERE lote_id = %s", (batch_id,))
        existing_lote = cur.fetchone()
        
        if existing_lote:
             lote_fk = existing_lote[0]
             logging.warning(f"Lote '{batch_id}' já existe no banco. Atualizando documentos...")
             cur.execute("DELETE FROM documentos WHERE lote_fk = %s", (lote_fk,))
        else:
             cur.execute("INSERT INTO lotes (lote_id, sumario) VALUES (%s, %s) RETURNING id", (batch_id, summary_json))
             lote_fk = cur.fetchone()[0]

        
        docs_data_to_insert = []
        
        if candidato_id:
            insert_query = """
            INSERT INTO documentos (id_candidate, lote_fk, arquivo, caminho, qualidade, categoria, dados_extraidos) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for doc in document_results:
                dados_extraidos_json = json.dumps(doc.get("dados_extraidos"), ensure_ascii=False) if doc.get("dados_extraidos") else None
                categoria = doc.get("categoria", "N/A") 
                docs_data_to_insert.append((
                    candidato_id, 
                    lote_fk, 
                    doc.get("arquivo", "Nome Indisponível"), 
                    doc.get("caminho", "Caminho Indisponível"), 
                    doc.get("qualidade", "Qualidade Indisponível"), 
                    categoria, 
                    dados_extraidos_json
                ))
        else:
            logging.warning(f"Nenhum candidato_id fornecido para o lote {batch_id}. Usando o DEFAULT do banco.")
            insert_query = """
            INSERT INTO documentos (lote_fk, arquivo, caminho, qualidade, categoria, dados_extraidos) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            for doc in document_results:
                dados_extraidos_json = json.dumps(doc.get("dados_extraidos"), ensure_ascii=False) if doc.get("dados_extraidos") else None
                categoria = doc.get("categoria", "N/A") 
                docs_data_to_insert.append((
                    lote_fk, 
                    doc.get("arquivo", "Nome Indisponível"), 
                    doc.get("caminho", "Caminho Indisponível"), 
                    doc.get("qualidade", "Qualidade Indisponível"), 
                    categoria, 
                    dados_extraidos_json
                ))
        
        if docs_data_to_insert:
             cur.executemany(insert_query, docs_data_to_insert)

        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Resultados do lote '{batch_id}' salvos/atualizados no banco de dados com sucesso.")
    except psycopg2.Error as db_err:
         logging.error(f"Erro de Banco de Dados ao salvar lote '{batch_id}': {db_err}")
         if 'conn' in locals() and conn: 
              conn.rollback() 
    except Exception as e:
        logging.error(f"Erro geral ao salvar o lote '{batch_id}' no banco de dados: {e}")
        if 'conn' in locals() and conn: 
              conn.rollback()
    finally:
         if 'cur' in locals() and cur:
              cur.close()
         if 'conn' in locals() and conn:
              conn.close()


def _processar_documento_individual(item, config):
    """
    Função "worker" que processa um único documento. 
    (Esta função NÃO chama init_models() - os modelos são globais)
    """
    
    if isinstance(item, dict) and 'path' in item:
         path = item['path']
    elif isinstance(item, str):
         path = item
    else:
         logging.error(f"Item inválido na lista de ficheiros: {item}")
         return None 

    abs_path = os.path.abspath(path)
    logging.info(f"[INÍCIO] Processando ficheiro: {os.path.basename(abs_path)}")
    result = {"arquivo": os.path.basename(abs_path), "caminho": abs_path} 

    if isinstance(item, dict) and 'error' in item:
        result.update({"qualidade": f"Reprovado (Erro na conversão: {item['error']})", "categoria": "N/A", "dados_extraidos": None})
        logging.info(f"[FIM] Documento com erro: {os.path.basename(abs_path)}")
    elif not os.path.exists(abs_path):
         result.update({"qualidade": "Reprovado (Ficheiro não encontrado após conversão)", "categoria": "N/A", "dados_extraidos": None})
         logging.info(f"[FIM] Ficheiro não encontrado: {os.path.basename(abs_path)}")
    else:
        try:
            logging.info(f"[QUALIDADE] Avaliando qualidade de: {os.path.basename(abs_path)}")
            result["qualidade"] = assess_quality(abs_path, config)
            logging.info(f"[QUALIDADE] Resultado: {result['qualidade']}")
            
            if "Aprovado" in result["qualidade"]:
                # Esta função (classify_document_with_ocr) usa os modelos globais
                logging.info(f"[CLASSIFICAÇÃO] Classificando: {os.path.basename(abs_path)}")
                result["categoria"] = classify_document_with_ocr(abs_path, config)
                logging.info(f"[CLASSIFICAÇÃO] Categoria: {result['categoria']}")
                
                if "Erro" not in result["categoria"]: 
                    # Esta função (extract_data) usa os modelos globais
                    logging.info(f"[EXTRAÇÃO] Extraindo dados de: {os.path.basename(abs_path)}")
                    result["dados_extraidos"] = extract_data(abs_path, result["categoria"], config)
                    logging.info(f"[EXTRAÇÃO] Dados extraídos: {bool(result['dados_extraidos'])}")
                else:
                     result["dados_extraidos"] = None
            else:
                result.update({"categoria": "N/A", "dados_extraidos": None})
                logging.info(f"[QUALIDADE] Documento reprovado, sem extração")
        except Exception as proc_err:
             logging.error(f"[ERRO] Erro inesperado ao processar '{os.path.basename(abs_path)}': {proc_err}")
             result.update({"qualidade": "Reprovado (Erro no processamento)", "categoria": "N/A", "dados_extraidos": None})
    
    logging.info(f"[FIM] Processamento concluído para: {os.path.basename(abs_path)}")
    return result


def run_analysis_for_batch(batch_id, candidato_id=None):
    """
    Função principal que executa a análise completa para um único lote.
    Agora usa ThreadPoolExecutor para paralelismo seguro de memória.
    """
    
    # --- MUDANÇA AQUI: init_models() é chamado ANTES do pool ---
    init_models() # Carrega os modelos de IA no processo principal
    
    config = load_config() 
    if not config:
        return {"status": "error", "message": "Configuração não encontrada"}

    input_folder = config["folder_paths"]["input"]
    output_folder = config["folder_paths"]["output"]
    batch_folder_path = os.path.abspath(os.path.join(input_folder, batch_id))

    if not os.path.isdir(batch_folder_path):
        logging.error(f"Pasta do lote não encontrada em: {batch_folder_path}")
        return {"status": "error", "message": f"Lote {batch_id} não encontrado"}

    logging.info(f"Iniciando preparação de ficheiros para o lote: {batch_id}")
    batch_data = prepare_batch_files(batch_folder_path, config)
    
    if not batch_data['files']:
        logging.warning(f"Nenhum ficheiro válido encontrado ou convertido no lote {batch_id}")
        batch_results = []
    else:
        batch_results = []
        total_files = len(batch_data['files'])
        
        futures = []
        # --- MUDANÇA AQUI: Trocado Process por Thread ---
        # Limitado a 2 workers para evitar uso excessivo de RAM
        with ThreadPoolExecutor(max_workers=2) as executor:
            for item in batch_data['files']:
                futures.append(executor.submit(_processar_documento_individual, item, config))

            logging.info(f"Processando {total_files} arquivos em threads (aguardando conclusão)...")
            completed_count = 0
            future_to_item = {future: item for future, item in zip(futures, batch_data['files'])}
            try:
                for future in as_completed(futures, timeout=600):
                    try:
                        res = future.result(timeout=600)
                        if res:
                            batch_results.append(res)
                            completed_count += 1
                            logging.info(f"✅ Progresso: {completed_count}/{total_files} documentos concluídos")
                    except Exception as e:
                        item = future_to_item.get(future)
                        logging.error(f"❌ Uma tarefa de processamento de documento falhou: {e}")
                        batch_results.append({
                            "arquivo": os.path.basename(item if isinstance(item, str) else item.get('path', 'desconhecido')),
                            "caminho": os.path.abspath(item if isinstance(item, str) else item.get('path', '')),
                            "qualidade": f"Reprovado (Erro: {e})",
                            "categoria": "N/A",
                            "dados_extraidos": None
                        })
                        completed_count += 1
            except TimeoutError:
                # Marcar todos os futuros não finalizados como timeout
                unfinished = [f for f in futures if not f.done()]
                for future in unfinished:
                    item = future_to_item.get(future)
                    logging.error(f"❌ Timeout ao processar documento (mais de 10 minutos)")
                    batch_results.append({
                        "arquivo": os.path.basename(item if isinstance(item, str) else item.get('path', 'desconhecido')),
                        "caminho": os.path.abspath(item if isinstance(item, str) else item.get('path', '')),
                        "qualidade": "Reprovado (Timeout)",
                        "categoria": "N/A",
                        "dados_extraidos": None
                    })
                    completed_count += 1

            logging.info(f"✅ Processamento em threads concluído. Total processado: {len(batch_results)}/{total_files}")


    logging.info("Gerando sumário do lote...")
    batch_summary = generate_batch_summary(batch_id, batch_results, config)
    
    print("\n--- SUMÁRIO EXECUTIVO DO LOTE ---")
    print(json.dumps(batch_summary, indent=4, ensure_ascii=False))
    print("---------------------------------\n")

    manage_db_connection(config, batch_id, batch_summary, batch_results, candidato_id) 

    output_path_base = os.path.abspath(output_folder)
    output_path_lote = os.path.join(output_path_base, batch_id)
    
    if not os.path.exists(output_path_base):
        os.makedirs(output_path_base)
        logging.info(f"Pasta de saída criada: {output_path_base}")
        
    try:
        if os.path.exists(output_path_lote):
             logging.warning(f"A pasta de destino '{output_path_lote}' já existe. Sobrescrevendo/movendo conteúdo...")
             shutil.move(batch_folder_path, output_path_lote)
        else:
            shutil.move(batch_folder_path, output_path_lote)
            
        logging.info(f"Lote '{batch_id}' movido para a pasta de processados: {output_path_lote}")
    except Exception as e:
        logging.error(f"Não foi possível mover o lote '{batch_id}' de '{batch_folder_path}' para '{output_path_lote}': {e}")
        return {"status": "warning", "message": f"Lote {batch_id} processado, mas falha ao mover pasta."}

    return {"status": "success", "message": f"Lote {batch_id} processado."}