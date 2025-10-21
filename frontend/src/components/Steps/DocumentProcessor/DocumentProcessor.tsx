import React, { useState } from 'react';
import axios from 'axios';
import Button from '../../Button/Button';
import Badge from '../../badge/Badge';
import { supabase } from '../../../supabaseClient';
import './DocumentProcessor.scss';

interface DocumentFile {
  file: File | null;
  uploaded: boolean;
  processing: boolean;
  processed: boolean;
  result?: any;
}

interface DocumentProcessorProps {
  candidatoId: string;
  onStepChange?: (novoStep: number) => void;
}

const DocumentProcessor: React.FC<DocumentProcessorProps> = ({ candidatoId, onStepChange }) => {
  const [documents, setDocuments] = useState<{
    rg: DocumentFile;
    cpf: DocumentFile;
    comprovante_endereco: DocumentFile;
  }>({
    rg: { file: null, uploaded: false, processing: false, processed: false },
    cpf: { file: null, uploaded: false, processing: false, processed: false },
    comprovante_endereco: { file: null, uploaded: false, processing: false, processed: false }
  });

  const documentLabels = {
    rg: 'RG (Carteira de Identidade)',
    cpf: 'CPF',
    comprovante_endereco: 'Comprovante de Endereço'
  };

  const handleFileChange = (docType: keyof typeof documents, file: File) => {
    setDocuments(prev => ({
      ...prev,
      [docType]: {
        ...prev[docType],
        file,
        uploaded: true
      }
    }));
  };

  const processDocument = async (docType: keyof typeof documents) => {
    const doc = documents[docType];
    if (!doc.file) return;

    setDocuments(prev => ({
      ...prev,
      [docType]: { ...prev[docType], processing: true }
    }));

    try {
      const formData = new FormData();
      formData.append('document', doc.file);
      formData.append('document_type', docType);
      formData.append('candidato_id', candidatoId);

      const response = await axios.post('http://127.0.0.1:5002/api/process-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000 // 30 segundos
      });

      setDocuments(prev => ({
        ...prev,
        [docType]: {
          ...prev[docType],
          processing: false,
          processed: true,
          result: response.data
        }
      }));

      console.log(`${docType} processado:`, response.data);
    } catch (error) {
      console.error(`Erro ao processar ${docType}:`, error);
      setDocuments(prev => ({
        ...prev,
        [docType]: { ...prev[docType], processing: false }
      }));
      alert(`Erro ao processar ${documentLabels[docType]}: ${error.response?.data?.error || error.message}`);
    }
  };

  const processAllDocuments = async () => {
    const documentsToProcess = Object.keys(documents).filter(
      key => documents[key as keyof typeof documents].uploaded && !documents[key as keyof typeof documents].processed
    );

    for (const docType of documentsToProcess) {
      await processDocument(docType as keyof typeof documents);
    }

    // Verificar se todos foram processados
    const allProcessed = Object.values(documents).every(doc => !doc.uploaded || doc.processed);
    
    if (allProcessed && onStepChange) {
      alert('Todos os documentos foram processados com sucesso!');
      onStepChange(4);
    }
  };

  const getBadgeStatus = (doc: DocumentFile) => {
    if (doc.processing) return <Badge color='warning' text='Processando...' />;
    if (doc.processed) return <Badge color='success' text='Processado' />;
    if (doc.uploaded) return <Badge color='info' text='Anexado' />;
    return <Badge color='error' text='Pendente' />;
  };

  return (
    <div className="document-processor">
      <h3>Upload e Processamento de Documentos</h3>
      <p>Faça upload dos seus documentos para análise automática:</p>
      
      <div className="document-list">
        {Object.entries(documents).map(([docType, doc]) => (
          <div className="document-card" key={docType}>
            <div className="document-info">
              <div className="document-title">
                <span className="doc-name">{documentLabels[docType as keyof typeof documentLabels]}</span>
              </div>
              <div className="document-category">Documento de Identificação</div>
            </div>
            
            <div className="document-actions">
              <div className="badge-wrapper">
                {getBadgeStatus(doc)}
              </div>
              
              <label className="custom-file-label">
                <span className="file-icon">📎</span>
                <span>
                  {doc.file?.name || "Selecionar arquivo"}
                </span>
                <input
                  type="file"
                  className="file-input"
                  accept="image/*,.pdf"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileChange(docType as keyof typeof documents, e.target.files[0]);
                    }
                  }}
                  disabled={doc.processing}
                />
              </label>
              
              {doc.uploaded && !doc.processed && (
                <Button
                  onClick={() => processDocument(docType as keyof typeof documents)}
                  text={doc.processing ? 'Processando...' : 'Processar'}
                  color='secondary'
                  disabled={doc.processing}
                />
              )}
            </div>
            
            {doc.result && (
              <div className="document-result">
                <h4>Dados Extraídos:</h4>
                <pre>{JSON.stringify(doc.result, null, 2)}</pre>
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="action-buttons">
        <Button
          onClick={processAllDocuments}
          text='Processar Todos os Documentos'
          color='primary'
          disabled={Object.values(documents).some(doc => doc.processing) || 
                   !Object.values(documents).some(doc => doc.uploaded)}
        />
      </div>
    </div>
  );
};

export default DocumentProcessor;