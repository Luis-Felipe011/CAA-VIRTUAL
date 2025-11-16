import React, { useState } from 'react';
import { useToast } from '../../../context/ToastContext';
import Button from '../../Button/Button';
import Badge from '../../badge/Badge';
import './DocumentProcessor.scss';

// --- CONFIGURAÇÃO DOS SLOTS INDIVIDUAIS ---
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
}

interface DocumentProcessorProps {
  candidatoId?: string | null;
  onProcessamentoIniciado: (batchId: string) => void;
}

const DocumentProcessor: React.FC<DocumentProcessorProps> = ({ candidatoId, onProcessamentoIniciado }) => {
  // Estado para os slots fixos (RG, CPF, etc.)
  const [documents, setDocuments] = useState<Record<DocKey, DocumentFile>>({
    rg: { file: null, uploaded: false },
    comprovante_renda: { file: null, uploaded: false },
    certidao_nascimento: { file: null, uploaded: false },
    comprovante_residencia: { file: null, uploaded: false }
  });

  // Estado para arquivos extras (Upload em Massa)
  const [extraFiles, setExtraFiles] = useState<File[]>([]);
  
  const { showToast } = useToast();
  const [isProcessando, setIsProcessando] = useState(false);

  // --- HANDLERS PARA SLOTS INDIVIDUAIS ---
  const handleSlotFileChange = (docType: DocKey, file: File) => {
    setDocuments((prev) => ({
      ...prev,
      [docType]: { file, uploaded: true }
    }));
  };

  // --- HANDLERS PARA UPLOAD EM MASSA ---
  const handleBulkSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const newFiles = Array.from(event.target.files);
      setExtraFiles(prev => {
        // Evita duplicatas por nome
        const combined = [...prev, ...newFiles];
        return combined.filter((file, index, self) =>
          index === self.findIndex((f) => f.name === file.name)
        );
      });
    }
  };

  const removeExtraFile = (fileName: string) => {
    setExtraFiles(prev => prev.filter(f => f.name !== fileName));
  };

  // --- ENVIO UNIFICADO ---
  const processarTodosDocumentos = async () => {
    // 1. Coleta arquivos dos slots fixos
    const slotFiles = (Object.values(documents) as DocumentFile[])
      .filter((doc) => doc.file)
      .map((doc) => doc.file!);

    // 2. Junta com arquivos extras
    const todosArquivos = [...slotFiles, ...extraFiles];

    // 3. Validação
    if (todosArquivos.length === 0) {
      showToast('Adicione pelo menos um documento (nos slots ou em massa).', 'error');
      return;
    }

    const formData = new FormData();
    todosArquivos.forEach((file) => { 
        formData.append('files', file); 
    });
    
    if (candidatoId) formData.append('candidato_id', candidatoId);

    setIsProcessando(true);

    try {
      const response = await fetch('http://localhost:5003/processar_documentos', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();

      if (response.status === 202 && data.batch_id) {
        showToast('Documentos enviados! A IA está analisando...', 'success');
        onProcessamentoIniciado(data.batch_id);
      } else {
         throw new Error(data.erro || "Erro ao enviar documentos.");
      }

    } catch (err: any) {
      showToast(err.message, 'error');
      setIsProcessando(false);
    }
  };

  return (
  <div className="document-processor">
      
      {/* --- ÁREA 1: UPLOAD EM MASSA (OPCIONAL) --- */}
      <div className="bulk-section">
        <h3>Envio Rápido (Opcional)</h3>
        <p className="helper-text">Tem muitos arquivos? Selecione todos de uma vez aqui. A IA vai identificar o que é cada um.</p>
        
        <label className="bulk-dropzone">
            <div className="icon">☁️</div>
            <span>Clique para selecionar múltiplos arquivos</span>
            <input 
                type="file" 
                multiple 
                accept="image/*,.pdf" 
                onChange={handleBulkSelect}
                disabled={isProcessando}
            />
        </label>

        {extraFiles.length > 0 && (
            <ul className="extra-files-list">
                {extraFiles.map(f => (
                    <li key={f.name}>
                        <span>📄 {f.name}</span>
                        <button onClick={() => removeExtraFile(f.name)} disabled={isProcessando}>×</button>
                    </li>
                ))}
            </ul>
        )}
      </div>

      <div className="divider"><span>OU USE OS SLOTS ABAIXO</span></div>

      {/* --- ÁREA 2: SLOTS INDIVIDUAIS (COMO ESTAVA ANTES) --- */}
      <div className="slots-list">
        {Object.entries(documents).map(([docType, doc]) => (
          <div className="document-card" key={docType}>
            <div className="document-info">
              <div className="document-title">
                <span className="doc-name">{documentLabels[docType as DocKey]}</span>
              </div>
            </div>
            <div className="document-actions">
              <div className="badge-wrapper">
                {doc.uploaded ? <Badge color='info' text='Pronto para Envio' /> : <Badge color='danger' text='Pendente' />}
              </div>
              <label className="custom-file-label">
                <span className="file-icon">📎</span>
                <span>{doc.file?.name || "Selecionar arquivo"}</span>
                <input
                  type="file"
                  className="file-input"
                  accept="image/*,.pdf"
                  onChange={(e) => e.target.files?.[0] && handleSlotFileChange(docType as DocKey, e.target.files[0])}
                  disabled={isProcessando}
                />
              </label>
            </div>
          </div>
        ))}
      </div>

      {/* BOTÃO FINAL DE ENVIO */}
      <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <Button
            onClick={processarTodosDocumentos}
            text={isProcessando ? "Enviando..." : "Processar Tudo"}
            color="primary"
            size="large"
          />
      </div>
    </div>
  );
};

export default DocumentProcessor;