import React, { useState } from 'react';
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

const DocumentProcessor: React.FC = () => {
  const [documents, setDocuments] = useState<Record<DocKey, DocumentFile>>({
    rg: { file: null, uploaded: false, processing: false, processed: false },
    comprovante_renda: { file: null, uploaded: false, processing: false, processed: false },
    certidao_nascimento: { file: null, uploaded: false, processing: false, processed: false },
    comprovante_residencia: { file: null, uploaded: false, processing: false, processed: false }
  });

  const processarTodosDocumentos = async () => {
    const arquivos = (Object.values(documents) as DocumentFile[])
      .filter((doc) => doc.file)
      .map((doc) => doc.file);

    if (arquivos.length === 0) {
      alert('Adicione pelo menos um documento para processar.');
      return;
    }

    const formData = new FormData();
    arquivos.forEach((file) => {
      formData.append('files', file!);
    });

    try {
      const response = await fetch('http://localhost:5003/processar_documentos', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      setDocuments((prev) => {
        const novo = { ...prev };
        Object.keys(novo).forEach((key) => {
          if (novo[key as DocKey].file) {
            novo[key as DocKey].processed = true;
            novo[key as DocKey].result = result;
          }
        });
        return novo;
      });
      alert('Processamento concluído! Veja o console para detalhes.');
      console.log(result);
      // Avançar para a próxima etapa
      window.dispatchEvent(new CustomEvent('proximaEtapa'));
    } catch (err) {
      alert('Erro ao processar documentos.');
    }
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

  const processDocument = async (docType: DocKey) => {
    setDocuments((prev) => ({
      ...prev,
      [docType]: {
        ...prev[docType],
        processing: true
      }
    }));
    setTimeout(() => {
      setDocuments((prev) => ({
        ...prev,
        [docType]: {
          ...prev[docType],
          processing: false,
          processed: true,
          result: { status: 'ok', nome: 'Exemplo', tipo: docType }
        }
      }));
    }, 1500);
  };

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
                  disabled={doc.processing}
                />
              </label>
              {doc.uploaded && !doc.processed && (
                <Button
                  onClick={() => processDocument(docType as DocKey)}
                  text={doc.processing ? 'Processando...' : 'Processar'}
                  color='secondary'
                />
              )}
            </div>
            {doc.result && (
              <div className="document-result">
                <pre>{JSON.stringify(doc.result, null, 2)}</pre>
              </div>
            )}
          </div>
        ))}
        <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <Button
            onClick={processarTodosDocumentos}
            text="Processar Todos"
            color="primary"
          />
        </div>
      </div>
    </div>
  );
};

export default DocumentProcessor;