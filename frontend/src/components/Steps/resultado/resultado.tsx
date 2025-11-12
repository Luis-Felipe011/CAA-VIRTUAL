import React, { useEffect, useState, useCallback } from "react";
import { supabase } from "../../../supabaseClient";
import "./resultado.scss";

// Tipos
interface FileEntry {
  fileName: string;
  publicUrl: string;
  status?: "aceito" | "recusado"; 
  motivoRecusa?: string;
  dados_extraidos?: Record<string, string>; // Novo campo para armazenar os dados
}

interface ResultadoProps {
  candidatoId: string;
  batchId: string | null;
}

interface DocumentoBackend {
  arquivo: string;
  qualidade: string;
  categoria: string;
  dados_extraidos: any;
}

const Resultado: React.FC<ResultadoProps> = ({ candidatoId }) => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [reenviando, setReenviando] = useState<string | null>(null);

  // Estados para o Modal de Edição
  const [editingDoc, setEditingDoc] = useState<FileEntry | null>(null);
  const [editFormData, setEditFormData] = useState<Record<string, string>>({});
  const [savingData, setSavingData] = useState(false);

  const fetchFilesAndStatus = useCallback(async () => {
    if (!candidatoId) return;
    setLoading(true);
    
    // 1. Busca ficheiros do Storage (URLs)
    const bucket = supabase.storage.from("documents");
    const { data: docFolders } = await bucket.list(`candidato_${candidatoId}`, { limit: 100 });
    let allFiles: FileEntry[] = [];
    
    if (docFolders) {
      for (const docFolder of docFolders) {
        const docPath = `candidato_${candidatoId}/${docFolder.name}`;
        const { data: items } = await bucket.list(docPath, { limit: 100 });
        if (!items) continue;
        for (const item of items) {
          const filePath = `${docPath}/${item.name}`;
          const { data } = bucket.getPublicUrl(filePath);
          allFiles.push({
            fileName: item.name,
            publicUrl: data.publicUrl,
          });
        }
      }
    }

    // 2. Busca TODOS os dados extraídos do backend (para preencher o modal)
    let dadosDoBackend: DocumentoBackend[] = [];
    try {
        const res = await fetch(`http://localhost:5003/candidato/${candidatoId}/todos_documentos`);
        if (res.ok) {
            const json = await res.json();
            dadosDoBackend = json.documentos || [];
        }
    } catch (e) { console.error(e); }

    // 3. Busca status do funcionário (se houver)
    const { data: statusData } = await supabase
      .from('document_status') 
      .select('file_path, status, justificativa')
      .eq('candidato_id', candidatoId);

    const statusMap = new Map<string, { status: "aceito" | "recusado", motivo: string }>();
    if (statusData) {
      for (const row of statusData) {
        statusMap.set(row.file_path, { status: row.status, motivo: row.justificativa || "" });
      }
    }

    // 4. Combina tudo
    const filesWithData = allFiles.map(f => {
      const docData = dadosDoBackend.find(d => d.arquivo === f.fileName);
      const dbStatus = statusMap.get(f.publicUrl);
      
      let finalStatus = undefined;
      let finalMotivo = undefined;

      if (dbStatus) {
        finalStatus = dbStatus.status;
        finalMotivo = dbStatus.motivo;
      } else if (docData && docData.qualidade.includes("Reprovado")) {
         finalStatus = "recusado";
         finalMotivo = docData.qualidade;
      }

      return {
        ...f,
        status: finalStatus as "aceito" | "recusado" | undefined,
        motivoRecusa: finalMotivo,
        dados_extraidos: docData?.dados_extraidos || null
      };
    });

    setFiles(filesWithData);
    setLoading(false);
  }, [candidatoId]);

  useEffect(() => { fetchFilesAndStatus(); }, [fetchFilesAndStatus]);

  // Função de Reenvio
  const handleReenvio = (arquivo: string, file: File) => {
    if (!candidatoId) return;
    setReenviando(arquivo);
    const formData = new FormData();
    formData.append("files", file, arquivo); 
    formData.append("candidato_id", candidatoId);
    
    fetch("http://localhost:5003/processar_documentos", { method: "POST", body: formData })
    .then(res => res.json())
    .then(data => {
        setReenviando(null);
        if (data.status === "processamento_iniciado") {
            alert("Reenviado! Atualize a página em alguns instantes.");
            setFiles((prev) => prev.filter((d) => d.fileName !== arquivo));
        } else { alert("Erro: " + data.erro); }
    })
    .catch(() => { setReenviando(null); alert("Erro de rede."); });
  };

  // Funções do Modal de Edição
  const openEditModal = (doc: FileEntry) => {
    if (!doc.dados_extraidos) {
        alert("Não há dados extraídos para este documento.");
        return;
    }
    setEditingDoc(doc);
    setEditFormData({ ...doc.dados_extraidos });
  };

  const handleInputChange = (key: string, value: string) => {
    setEditFormData(prev => ({ ...prev, [key]: value }));
  };

  const saveEditedData = async () => {
    if (!editingDoc || !candidatoId) return;
    setSavingData(true);
    try {
        const res = await fetch("http://localhost:5003/documento/dados", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                candidato_id: candidatoId,
                arquivo: editingDoc.fileName,
                dados: editFormData
            })
        });
        const json = await res.json();
        if (json.status === "sucesso") {
            alert("Dados atualizados e confirmados!");
            setEditingDoc(null); // Fecha modal
            fetchFilesAndStatus(); // Recarrega
        } else {
            alert("Erro ao salvar: " + json.erro);
        }
    } catch (e) { alert("Erro de rede."); }
    setSavingData(false);
  };

  const aceitos = files.filter(f => f.status === "aceito");
  const rejeitados = files.filter(f => f.status === "recusado");
  const pendentes = files.filter(f => !f.status);

  return (
    <div className="resultado-container">
      <h2>Resultado da Análise</h2>
      {loading ? <div className="loading">Carregando...</div> : (
        <div className="document-list">
          
          {/* MODAL DE EDIÇÃO */}
          {editingDoc && (
            <div className="modal-overlay">
                <div className="modal-content edit-modal">
                    <div className="modal-header">
                        <h3>Conferir Dados: {editingDoc.fileName}</h3>
                        <button className="close-btn" onClick={() => setEditingDoc(null)}>×</button>
                    </div>
                    <div className="modal-body">
                        <p className="info-text">Verifique se os dados extraídos pela IA estão corretos. Edite se necessário.</p>
                        <div className="fields-grid">
                            {Object.entries(editFormData).map(([key, value]) => (
                                <div key={key} className="field-group">
                                    <label>{key}</label>
                                    <input 
                                        type="text" 
                                        value={value} 
                                        onChange={(e) => handleInputChange(key, e.target.value)}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button className="cancel-btn" onClick={() => setEditingDoc(null)}>Cancelar</button>
                        <button className="save-btn" onClick={saveEditedData} disabled={savingData}>
                            {savingData ? "Salvando..." : "Confirmar e Salvar"}
                        </button>
                    </div>
                </div>
            </div>
          )}

          {/* CARTÕES */}
          {[...rejeitados, ...pendentes, ...aceitos].map(f => (
             <div className={`document-card resultado-card ${f.status || 'pendente'}`} key={f.fileName}>
                <div className="document-info">
                    <div className="document-title">
                        <span className="file-icon">📄</span>
                        <span className="doc-name">{f.fileName}</span>
                    </div>
                    {f.motivoRecusa && <div className="justificativa">Motivo: {f.motivoRecusa}</div>}
                </div>
                <div className="document-actions">
                    <a href={f.publicUrl} target="_blank" rel="noopener noreferrer" className="visualizar-link">Visualizar</a>
                    
                    {/* Botão Conferir Dados (Só aparece se houver dados extraídos) */}
                    {f.dados_extraidos && (
                        <button className="conferir-btn" onClick={() => openEditModal(f)}>
                            Conferir Dados
                        </button>
                    )}

                    {/* Status Badge */}
                    {f.status === 'aceito' && <span className="badge badge-aceito">Aceito</span>}
                    {f.status === 'recusado' && (
                        <div className="reenvio-wrapper">
                            <span className="badge badge-rejeitado">Rejeitado</span>
                            <label className="reenvio-label">
                                {reenviando === f.fileName ? "Enviando..." : "Reenviar"}
                                <input type="file" hidden onChange={e => e.target.files?.[0] && handleReenvio(f.fileName, e.target.files[0])} disabled={!!reenviando} />
                            </label>
                        </div>
                    )}
                    {!f.status && <span className="badge badge-pendente">Em Análise</span>}
                </div>
             </div>
          ))}
          
          {files.length === 0 && <p className="vazio">Nenhum documento encontrado.</p>}
        </div>
      )}
    </div>
  );
};

export default Resultado;