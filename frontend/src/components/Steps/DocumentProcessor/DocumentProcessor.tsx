import React, { useState } from 'react';
import { useToast } from '../../../context/ToastContext';
import Button from '../../Button/Button';
import Badge from '../../badge/Badge';
import './DocumentProcessor.scss';

const documentLabels = {
  rg: 'RG (Carteira de Identidade)',
  comprovante_renda: 'Comprovante de Renda',
  certidao_nascimento: 'Certidão de Nascimento',
  comprovante_residencia: 'Comprovante de Residência'
};

type DocKey = keyof typeof documentLabels;

interface DocumentFile {
  file: File | null;
  uploaded: boolean;
  processing: boolean;
  processed: boolean;
}

interface DocumentProcessorProps {
  candidatoId?: string | null;
  onProcessamentoIniciado: (batchId: string) => void;
}

const DocumentProcessor: React.FC<DocumentProcessorProps> = ({ candidatoId, onProcessamentoIniciado }) => {
  const [documents, setDocuments] = useState<Record<DocKey, DocumentFile>>({
    rg: { file: null, uploaded: false, processing: false, processed: false },
    comprovante_renda: { file: null, uploaded: false, processing: false, processed: false },
    certidao_nascimento: { file: null, uploaded: false, processing: false, processed: false },
    comprovante_residencia: { file: null, uploaded: false, processing: false, processed: false }
  });

  const { showToast } = useToast();
  const [isProcessando, setIsProcessando] = useState(false);

  const processarTodosDocumentos = async () => {
    const arquivos = (Object.values(documents) as DocumentFile[])
      .filter((doc) => doc.file)
      .map((doc) => doc.file);

    if (arquivos.length === 0) {
      showToast('Adicione pelo menos um documento.', 'error');
      return;
    }

    const formData = new FormData();
    arquivos.forEach((file) => { formData.append('files', file!); });
    
    if (candidatoId) formData.append('candidato_id', candidatoId);

    setIsProcessando(true); // Ativa loading do botão

    try {
      const response = await fetch('http://localhost:5003/processar_documentos', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();

      if (response.status === 202 && data.batch_id) {
        showToast('Documentos enviados! Iniciando análise...', 'success');
        // AQUI É O SEGREDO: Passa o batch_id para a Home
        onProcessamentoIniciado(data.batch_id);
      } else {
         throw new Error(data.erro || "Erro ao enviar documentos.");
      }

    } catch (err: any) {
      showToast(err.message, 'error');
      setIsProcessando(false);
    }
  };

  const handleFileChange = (docType: DocKey, file: File) => {
    setDocuments((prev) => ({
      ...prev,
      [docType]: { ...prev[docType], file, uploaded: true }
    }));
  };

  return (
  <div className="document-processor">
      <div className="document-list">
        {Object.entries(documents).map(([docType, doc]) => (
          <div className="document-card" key={docType}>
            <div className="document-info">
              <div className="document-title">
                <span className="doc-name">{documentLabels[docType as DocKey]}</span>
              </div>
            </div>
            <div className="document-actions">
              <div className="badge-wrapper">
                {doc.uploaded ? <Badge color='info' text='Anexado' /> : <Badge color='danger' text='Pendente' />}
              </div>
              <label className="custom-file-label">
                <span className="file-icon">📎</span>
                <span>{doc.file?.name || "Selecionar arquivo"}</span>
                <input
                  type="file"
                  className="file-input"
                  accept="image/*,.pdf"
                  onChange={(e) => e.target.files?.[0] && handleFileChange(docType as DocKey, e.target.files[0])}
                  disabled={isProcessando}
                />
              </label>
            </div>
          </div>
        ))}
        <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <Button
            onClick={processarTodosDocumentos}
            text={isProcessando ? "Enviando..." : "Processar Todos"}
            color="primary"
            
          />
        </div>
      </div>
    </div>
  );
};

export default DocumentProcessor;