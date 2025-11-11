import React, { useEffect, useState, useRef } from "react";
import Modal from '../../Modal/Modal';

// Componente para documento rejeitado com opção de reenvio
const RejeitadoCard: React.FC<{ file: FileEntry; candidatoId: string; onReenviado?: () => void }> = ({ file, candidatoId, onReenviado }) => {
  const [reenviando, setReenviando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setReenviando(true);
    setSucesso(false);
    const ok = await reenviarDocumento(e.target.files[0], candidatoId, file.fileName);
    setReenviando(false);
    setSucesso(ok);
    if (ok && onReenviado) onReenviado();
  };

  return (
    <div className="document-card resultado-card rejeitado">
      <div className="document-info">
        <div className="document-title">
          <span className="file-icon">📎</span>
          <span className="doc-name">{file.fileName}</span>
        </div>
      </div>
      <div className="document-actions">
        <span className="badge badge-rejeitado">Rejeitado</span>
        <button
          className="reenviar-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={reenviando}
          style={{ marginLeft: 12 }}
        >
          {reenviando ? 'Enviando...' : 'Reenviar'}
        </button>
        <input
          type="file"
          accept="image/*,application/pdf"
          style={{ display: 'none' }}
          ref={fileInputRef}
          onChange={handleFileChange}
        />
        {sucesso && <span className="reenviar-sucesso">Enviado!</span>}
      </div>
    </div>
  );
};
// Função auxiliar para upload de arquivo reprovado
async function reenviarDocumento(file: File, candidatoId: string, fileName: string) {
  const formData = new FormData();
  formData.append('files', file, fileName);
  formData.append('candidato_id', candidatoId);
  // Ajuste a URL se necessário
  const res = await fetch('http://localhost:5003/processar_documentos', {
    method: 'POST',
    body: formData,
  });
  return res.ok;
}
import { supabase } from "../../../supabaseClient";
import "./resultado.scss";

interface FileEntry {
  fileName: string;
  publicUrl: string;
  status?: string;
}

interface ResultadoProps {
  batchId: string | null;
  candidatoId: string;
  onStepChange?: (step: number) => void;
}

const Resultado: React.FC<ResultadoProps> = ({ batchId, candidatoId, onStepChange }) => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [dadosExtraidos, setDadosExtraidos] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [analiseStatus, setAnaliseStatus] = useState<'analise'|'concluido'|'erro'>('analise');
  const pollingRef = useRef<NodeJS.Timeout|null>(null);
  const [showedStep, setShowedStep] = useState(false);

  useEffect(() => {
    // Função para buscar o resultado da análise do backend (polling)
    const fetchResultadoLote = async () => {
      setLoading(true);
      try {
        if (!batchId) return;
        const res = await fetch(`http://localhost:5003/resultado_lote/${batchId}`);
        if (res.ok) {
          const data = await res.json();
          console.log('DEBUG resultado_lote:', data); // <-- LOG DE DEBUG
          if (data.status === 'concluido') {
            setAnaliseStatus('concluido');
            const filesBackend: FileEntry[] = (data.documentos || []).map((doc: any) => ({
              fileName: doc.arquivo,
              publicUrl: '',
              status: doc.qualidade && doc.qualidade.toLowerCase().includes('aprovado') ? 'aceito' : 'recusado',
            }));
            setFiles(filesBackend);
            // Coletar dados extraídos dos documentos aprovados
            const extraidos = (data.documentos || [])
              .filter((doc: any) => doc.qualidade && doc.qualidade.toLowerCase().includes('aprovado') && doc.dados_extraidos)
              .map((doc: any) => doc.dados_extraidos ? JSON.parse(doc.dados_extraidos) : {});
            setDadosExtraidos(extraidos);
            setLoading(false);
            if (extraidos.length > 0) setShowModal(true);
            if (pollingRef.current) clearTimeout(pollingRef.current);
            return;
          } else {
            setAnaliseStatus('analise');
          }
        } else {
          setAnaliseStatus('erro');
        }
      } catch {
        setAnaliseStatus('erro');
      }
      setLoading(true);
      pollingRef.current = setTimeout(fetchResultadoLote, 3000);
    };
    if (batchId) {
      fetchResultadoLote();
    }
    return () => {
      if (pollingRef.current) clearTimeout(pollingRef.current);
    };
  }, [batchId]);

  // Avança para etapa Resultado (5) quando análise concluir
  useEffect(() => {
    if (analiseStatus === 'concluido' && onStepChange && !showedStep) {
      onStepChange(5);
      setShowedStep(true);
    }
  }, [analiseStatus, onStepChange, showedStep]);

  const aceitos = files.filter(f => f.status === "aceito");
  const rejeitados = files.filter(f => f.status === "recusado");
  const aprovado = files.length > 0 && rejeitados.length === 0;

  return (
    <div className="resultado-container">
      <h2>Resultado da Análise</h2>
      {analiseStatus === 'analise' && (
        <div className="loading">Analisando documentos... Aguarde.</div>
      )}
      {analiseStatus === 'erro' && (
        <div className="loading">Erro ao buscar resultado. Tente novamente mais tarde.</div>
      )}
      {analiseStatus === 'concluido' && !loading && (
        <>
          <div className="resultado-summary">
            {aprovado ? (
              <div className="aprovado-msg">✅ Todos os documentos foram aprovados! Seu cadastro foi aprovado.</div>
            ) : (
              <div className="reprovado-msg">❌ Um ou mais documentos foram reprovados. Reenvie os documentos rejeitados abaixo.</div>
            )}
          </div>
          {aprovado && showModal && (
            <Modal onClose={() => setShowModal(false)}>
              <h2>Dados extraídos dos documentos</h2>
              {dadosExtraidos.map((dados, idx) => (
                <div key={idx} style={{marginBottom: '1rem', background: '#f7f7f7', padding: '1rem', borderRadius: 8}}>
                  {Object.entries(dados).map(([key, val]) => (
                    <div key={key}><strong>{key}:</strong> {val}</div>
                  ))}
                </div>
              ))}
            </Modal>
          )}
          <div className="document-list">
            <div className="resultado-bloco">
              <h3>Documentos Aceitos</h3>
              {aceitos.length === 0 ? (
                <p className="resultado-vazio">Nenhum documento aceito.</p>
              ) : (
                aceitos.map(f => (
                  <div className="document-card resultado-card aceito" key={f.fileName}>
                    <div className="document-info">
                      <div className="document-title">
                        <span className="file-icon">📎</span>
                        <span className="doc-name">{f.fileName}</span>
                      </div>
                    </div>
                    <div className="document-actions">
                      <span className="badge badge-aceito">Aceito</span>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="resultado-bloco">
              <h3>Documentos Rejeitados</h3>
              {rejeitados.length === 0 ? (
                <p className="resultado-vazio">Nenhum documento rejeitado.</p>
              ) : (
                rejeitados.map(f => (
                  <RejeitadoCard key={f.fileName} file={f} candidatoId={candidatoId} onReenviado={() => window.location.reload()} />
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Resultado;

