import React, { useEffect, useState, useCallback } from "react";
import { useToast } from "../../../context/ToastContext"; 
import "./resultado.scss";

interface DocumentoBackend {
  id: number; 
  arquivo: string;
  qualidade: string;
  categoria: string;
  dados_extraidos: any;
  lote_id?: string; // Novo campo vindo do backend
}

interface FileEntry extends DocumentoBackend {
  publicUrl?: string; 
  status?: "aceito" | "recusado";
  motivoRecusa?: string;
}

interface ResultadoProps {
  candidatoId: string;
  batchId: string | null;
}

const Resultado: React.FC<ResultadoProps> = ({ candidatoId }) => {
  const [documentos, setDocumentos] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [editingDoc, setEditingDoc] = useState<DocumentoBackend | null>(null);
  const [editFormData, setEditFormData] = useState<Record<string, string>>({});
  const [savingData, setSavingData] = useState(false);
  const [reenviando, setReenviando] = useState<string | null>(null);
  
  const { showToast } = useToast(); 

  const fetchResultados = useCallback(async () => {
    setLoading(true);

    try {
        const res = await fetch(`http://localhost:5003/candidato/${candidatoId || 'teste'}/todos_documentos`);
        let docsBackend: DocumentoBackend[] = [];
        
        if (res.ok) {
            const json = await res.json();
            docsBackend = json.documentos || [];
        }

        const docsProcessados = docsBackend.map((doc) => {
            // CONSTRÓI A URL LOCAL
            // Ex: http://localhost:5003/imagens/uuid_lote/arquivo.jpg
            const localUrl = doc.lote_id 
                ? `http://localhost:5003/imagens/${doc.lote_id}/${doc.arquivo}`
                : undefined;

            return {
                ...doc,
                publicUrl: localUrl, // Usa a URL local
                status: doc.qualidade.includes("Aprovado") ? "aceito" : "recusado",
                motivoRecusa: doc.qualidade.includes("Aprovado") ? "" : doc.qualidade
            } as FileEntry;
        });

        setDocumentos(docsProcessados);

    } catch (e) {
        console.error("Erro:", e);
        showToast("Erro ao carregar documentos.", "error");
    } finally {
        setLoading(false);
    }
  }, [candidatoId, showToast]);

  useEffect(() => {
    fetchResultados();
  }, [fetchResultados]);

  // ... (MANTENHA AS FUNÇÕES openEditModal, handleInputChange, saveEditedData e handleReenvio IGUAIS) ...
  // (Vou colar aqui para garantir que você tenha o arquivo completo correto)
  
  const openEditModal = (doc: DocumentoBackend) => {
    if (!doc.dados_extraidos) {
        showToast("Não há dados extraídos para este documento.", "info");
        return;
    }
    setEditingDoc(doc);
    let dados = doc.dados_extraidos;
    if (typeof dados === 'string') {
        try { dados = JSON.parse(dados); } catch { dados = {}; }
    }
    setEditFormData(dados || {});
  };

  const handleInputChange = (key: string, value: string) => {
    setEditFormData(prev => ({ ...prev, [key]: value }));
  };

  const saveEditedData = async () => {
    if (!editingDoc) return;
    setSavingData(true);
    try {
        const res = await fetch("http://localhost:5003/documento/dados", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                documento_id: editingDoc.id, 
                dados: editFormData
            })
        });
        
        const json = await res.json();
        if (res.ok && json.status === "sucesso") {
            showToast("Dados atualizados com sucesso!", "success");
            setEditingDoc(null);
            fetchResultados(); 
        } else {
            showToast(`Erro ao salvar: ${json.erro || "Desconhecido"}`, "error");
        }
    } catch (e) { 
        showToast("Erro de conexão com o servidor.", "error");
    }
    setSavingData(false);
  };

  const handleReenvio = (arquivo: string, file: File) => {
    if (!candidatoId) return;
    setReenviando(arquivo);
    const formData = new FormData();
    formData.append("files", file, arquivo); 
    formData.append("candidato_id", candidatoId);
    
    fetch("http://localhost:5003/processar_documentos", { 
        method: "POST", 
        body: formData 
    })
    .then(res => res.json())
    .then(data => {
        setReenviando(null);
        if (data.status === "processamento_iniciado") {
            showToast("Arquivo reenviado! A IA está analisando novamente.", "success");
        } else { 
            showToast(`Erro no envio: ${data.erro}`, "error"); 
        }
    })
    .catch(() => { 
        setReenviando(null); 
        showToast("Erro de rede ao reenviar.", "error"); 
    });
  };

  return (
    <div className="resultado-container">
      <h2>Resultado da Análise</h2>
      
      {loading ? <div className="loading-container"><p>Carregando resultados...</p></div> : (
        <div className="document-list">
          
          {/* MODAL DE EDIÇÃO COM IMAGEM */}
          {editingDoc && (
            <div className="modal-overlay">
                <div className="edit-modal" style={{maxWidth: '900px'}}> {/* Mais largo para caber a imagem */}
                    <div className="modal-header">
                        <h3>Conferência: {editingDoc.arquivo}</h3>
                        <button className="close-btn" onClick={() => setEditingDoc(null)}>×</button>
                    </div>
                    
                    <div className="modal-body" style={{display: 'flex', gap: '2rem'}}>
                        {/* LADO ESQUERDO: IMAGEM */}
                        <div style={{flex: 1, borderRight: '1px solid #eee', paddingRight: '1rem'}}>
                             {(editingDoc as FileEntry).publicUrl ? (
                                <img 
                                    src={(editingDoc as FileEntry).publicUrl} 
                                    alt="Documento original" 
                                    style={{width: '100%', maxHeight: '400px', objectFit: 'contain', borderRadius: '8px', border: '1px solid #ddd'}} 
                                />
                             ) : (
                                 <p style={{textAlign: 'center', color: '#999', marginTop: '2rem'}}>Imagem não disponível</p>
                             )}
                        </div>

                        {/* LADO DIREITO: FORMULÁRIO */}
                        <div style={{flex: 1}}>
                            <p className="info-text">Compare com a imagem e corrija se necessário.</p>
                            <div className="fields-grid">
                                {Object.entries(editFormData).map(([key, value]) => (
                                    <div key={key} className="field-group">
                                        <label>{key}</label>
                                        <input 
                                            type="text" 
                                            value={String(value)} 
                                            onChange={(e) => handleInputChange(key, e.target.value)}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    
                    <div className="modal-footer">
                        <button className="cancel-btn" onClick={() => setEditingDoc(null)}>Cancelar</button>
                        <button className="save-btn" onClick={saveEditedData} disabled={savingData}>
                            {savingData ? "Salvando..." : "Confirmar Alterações"}
                        </button>
                    </div>
                </div>
            </div>
          )}

          {/* LISTA */}
          {documentos.length === 0 ? (
              <p className="vazio">Nenhum documento encontrado para este candidato.</p>
          ) : (
              documentos.map(doc => (
                <div className={`document-card resultado-card ${doc.status}`} key={doc.id}>
                    <div className="document-info">
                        <div className="document-title">
                            <span className="file-icon">📄</span>
                            <span className="doc-name">{doc.arquivo}</span>
                        </div>
                        {doc.motivoRecusa ? (
                            <div className="justificativa">Motivo: {doc.motivoRecusa}</div>
                        ) : (
                            <div className="categoria-info">Tipo: <strong>{doc.categoria}</strong></div>
                        )}
                    </div>
                    <div className="document-actions">
                        {/* BOTÃO VISUALIZAR RESTAURADO (Abre noutra aba) */}
                        {doc.publicUrl && (
                             <a href={doc.publicUrl} target="_blank" className="visualizar-link">Ver Documento</a>
                        )}
                        
                        {doc.dados_extraidos && (
                            <button className="conferir-btn" onClick={() => openEditModal(doc)}>
                                Conferir & Corrigir
                            </button>
                        )}

                        {doc.status === 'recusado' && (
                             <label className="reenvio-label">
                                {reenviando === doc.arquivo ? "Enviando..." : "Reenviar"}
                                <input type="file" hidden onChange={e => e.target.files?.[0] && handleReenvio(doc.arquivo, e.target.files[0])} disabled={!!reenviando} />
                            </label>
                        )}

                        <span className={`badge badge-${doc.status}`}>
                            {doc.status === 'aceito' ? 'Processado' : 'Atenção'}
                        </span>
                    </div>
                </div>
              ))
          )}
        </div>
      )}
    </div>
  );
};

export default Resultado;