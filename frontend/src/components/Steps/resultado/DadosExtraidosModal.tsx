import React from "react";
import './DadosExtraidosModal.scss';

interface DadosExtraidosModalProps {
  open: boolean;
  onClose: () => void;
  dados: Array<{
    arquivo: string;
    categoria: string;
    dados_extraidos: any;
  }>;
}

const DadosExtraidosModal: React.FC<DadosExtraidosModalProps> = ({ open, onClose, dados }) => {
  if (!open) return null;
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Dados extraídos dos documentos</h2>
        <div className="dados-lista">
          {dados.map((doc, idx) => (
            <div key={idx} className="doc-extraido">
              <h4>{doc.categoria} ({doc.arquivo})</h4>
              <ul>
                {doc.dados_extraidos && typeof doc.dados_extraidos === 'object' ? (
                  Object.entries(doc.dados_extraidos).map(([campo, valor]) => (
                    <li key={campo}><strong>{campo}:</strong> {valor as string}</li>
                  ))
                ) : (
                  <li>Nenhum dado extraído.</li>
                )}
              </ul>
            </div>
          ))}
        </div>
        <button onClick={onClose} className="fechar-modal">Fechar</button>
      </div>
    </div>
  );
};

export default DadosExtraidosModal;
