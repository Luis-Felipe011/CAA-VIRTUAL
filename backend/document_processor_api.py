"""
API de Processamento de Documentos - Porta 5002
Exemplo de API que recebe documentos e processa usando OCR/IA
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import tempfile
import json

app = Flask(__name__)
CORS(app)

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'tiff', 'bmp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_rg_document(file_path):
    """Simula processamento de RG"""
    return {
        "tipo_documento": "RG",
        "numero_rg": "12.345.678-9",
        "nome": "João da Silva",
        "data_nascimento": "15/03/1990",
        "naturalidade": "São Paulo - SP",
        "filiacao": {
            "pai": "José da Silva",
            "mae": "Maria da Silva"
        },
        "orgao_expedidor": "SSP-SP",
        "data_expedicao": "20/01/2018",
        "confianca": 0.92
    }

def process_cpf_document(file_path):
    """Simula processamento de CPF"""
    return {
        "tipo_documento": "CPF",
        "numero_cpf": "123.456.789-00",
        "nome": "João da Silva",
        "data_nascimento": "15/03/1990",
        "situacao_cadastral": "REGULAR",
        "confianca": 0.95
    }

def process_comprovante_endereco(file_path):
    """Simula processamento de comprovante de endereço"""
    return {
        "tipo_documento": "COMPROVANTE_ENDERECO",
        "tipo_comprovante": "CONTA_LUZ",
        "endereco": {
            "logradouro": "Rua das Flores, 123",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "cep": "01234-567"
        },
        "data_vencimento": "15/11/2024",
        "valor": "R$ 85,43",
        "confianca": 0.88
    }

@app.route('/api/process-document', methods=['POST'])
def process_document():
    try:
        # Verificar se foi enviado um arquivo
        if 'document' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['document']
        document_type = request.form.get('document_type')
        candidato_id = request.form.get('candidato_id')
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo foi selecionado'}), 400
        
        if not document_type:
            return jsonify({'error': 'Tipo de documento não especificado'}), 400
        
        if file and allowed_file(file.filename):
            # Salvar arquivo temporariamente
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, f"{candidato_id}_{document_type}_{filename}")
            file.save(file_path)
            
            print(f"Processando documento: {document_type} para candidato: {candidato_id}")
            print(f"Arquivo salvo em: {file_path}")
            
            # Processar documento baseado no tipo
            if document_type == 'rg':
                result = process_rg_document(file_path)
            elif document_type == 'cpf':
                result = process_cpf_document(file_path)
            elif document_type == 'comprovante_endereco':
                result = process_comprovante_endereco(file_path)
            else:
                return jsonify({'error': f'Tipo de documento não suportado: {document_type}'}), 400
            
            # Adicionar metadados
            result['candidato_id'] = candidato_id
            result['arquivo_original'] = filename
            result['status'] = 'processado'
            result['timestamp'] = '2024-10-20T15:30:00Z'
            
            # Opcional: remover arquivo após processamento
            # os.remove(file_path)
            
            return jsonify({
                'success': True,
                'message': f'Documento {document_type} processado com sucesso',
                'data': result
            })
        else:
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
            
    except Exception as e:
        print(f"Erro ao processar documento: {str(e)}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'API de processamento de documentos está funcionando',
        'version': '1.0.0'
    })

@app.route('/api/supported-documents', methods=['GET'])
def supported_documents():
    return jsonify({
        'supported_types': ['rg', 'cpf', 'comprovante_endereco'],
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': '10MB'
    })

if __name__ == '__main__':
    print("Iniciando API de Processamento de Documentos na porta 5002...")
    print("Endpoints disponíveis:")
    print("  POST /api/process-document - Processar documento")
    print("  GET  /api/health - Status da API")
    print("  GET  /api/supported-documents - Tipos suportados")
    app.run(host='0.0.0.0', port=5002, debug=True)