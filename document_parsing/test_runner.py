# test_runner.py
import sys
import os

# Adiciona a pasta raiz (APRESENTACAO_ANALISE) ao caminho de busca do Python
# para que ele possa encontrar o pacote 'backend'
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# --- CORREÇÃO NA IMPORTAÇÃO ---
# Agora importamos especificando o caminho completo a partir da pasta raiz
try:
    from backend.document_parsing.analyzer import run_analysis_for_batch
except ModuleNotFoundError as e:
    print(f"ERRO: Não foi possível importar o módulo 'analyzer'.")
    print(f"Verifique se existem ficheiros '__init__.py' vazios nas pastas 'backend' e 'backend/document_parsing'.")
    print(f"Detalhes: {e}")
    # Imprime o caminho de busca atual do Python para ajudar na depuração
    print("\nCaminho de busca do Python (sys.path):")
    for p in sys.path:
        print(p)
    sys.exit(1) # Sai do script se a importação falhar
# --- FIM DA CORREÇÃO ---


if __name__ == "__main__":
    # --- PONTO DE CONFIGURAÇÃO ---
    LOTE_ID_PARA_TESTAR = "lote_para_teste"
    # ---------------------------

    print(f"--- INICIANDO ANÁLISE PARA O LOTE: '{LOTE_ID_PARA_TESTAR}' ---")

    # Chama a função principal
    resultado = run_analysis_for_batch(LOTE_ID_PARA_TESTAR)

    print("\n--- ANÁLISE CONCLUÍDA ---")
    print(f"Status Final: {resultado.get('status')}")
    print(f"Mensagem: {resultado.get('message')}")
    print("--------------------------")