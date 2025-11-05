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
  result?: any;
}

interface DocumentProcessorProps {
  candidatoId?: string | null;
  // --- NOVA PROP RECEBIDA DO home.tsx ---
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
  
  // --- ESTADO DE LOADING PARA O BOTÃO PRINCIPAL ---
  const [isProcessando, setIsProcessando] = useState(false);

  const processarTodosDocumentos = async () => {
    const arquivos = (Object.values(documents) as DocumentFile[])
      .filter((doc) => doc.file)
      .map((doc) => doc.file);

    if (arquivos.length === 0) {
      showToast('Adicione pelo menos um documento para processar.', 'error');
      return;
    }

    const formData = new FormData();

    arquivos.forEach((file) => {
      formData.append('files', file!);
    });
    if (candidatoId) {
      formData.append('candidato_id', candidatoId);
    }

    setIsProcessando(true); // Ativa o loading

    try {
      const response = await fetch('http://localhost:5003/processar_documentos', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json(); // Lê a resposta do backend

      if (!response.ok || response.status === 500) {
        throw new Error(data.erro || "Falha no servidor");
      }
      
      // --- LÓGICA CORRIGIDA ---
      if (response.status === 202 && data.status === "processamento_iniciado") {
        showToast('Documentos enviados para análise!', 'success');
        
        // Chama a função do 'home.tsx' para avançar a etapa
        // e passar o ID do lote que o backend acabou de criar
        onProcessamentoIniciado(data.batch_id); 
      } else {
         throw new Error("Resposta inesperada do servidor");
      }
      // --- FIM DA LÓGICA CORRIGIDA ---

    } catch (err: any) {
      showToast(err.message || 'Erro ao processar documentos.', 'error');
      setIsProcessando(false); // Desativa o loading em caso de erro
    }
    // Não desativamos o loading em caso de sucesso, pois a página vai mudar
  };

  const getBadgeStatus = (doc: DocumentFile) => {
    if (doc.processing) return <Badge color='warning' text='Processando...' />;
    if (doc.processed) return <Badge color='success' text='Processado' />;
    if (doc.uploaded) return <Badge color='info' text='Anexado' />;
    return <Badge color='danger' text='Pendente' />;
  };

  const handleFileChange = (docType: DocKey, file: File) => {
    setDocuments((prev) => ({
      ...prev,
      [docType]: {
        ...prev[docType],
        file,
        uploaded: true,
        processing: false,
        processed: false,
        result: undefined
      }
    }));
  };

  // Esta função não é mais necessária, pois processamos todos de uma vez
  // const processDocument = async (docType: DocKey) => { ... };

  return (
  <div className="document-processor" style={{ maxHeight: '80vh', overflowY: 'auto', padding: 0, background: '#fff', boxShadow: 'none', margin: 0 }}>
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
                      handleFileChange(docType as DocKey, e.target.files[0]);
                    }
                  }}
                  disabled={isProcessando} // Desativa todos se estiver processando
                />
              </label>
              {/* Removido o botão de processar individual */}
            </div>
          </div>
        ))}
        <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <Button
            onClick={processarTodosDocumentos}
            text={isProcessando ? "Enviando para análise..." : "Processar Todos"}
            color="primary"
            
          />
        </div>
      </div>
    </div>
  );
};

export default DocumentProcessor;