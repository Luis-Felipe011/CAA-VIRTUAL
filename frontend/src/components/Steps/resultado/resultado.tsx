import React, { useEffect, useState, useCallback } from "react";
import { useToast } from "../../../context/ToastContext"; // Importa o Toast
import "./resultado.scss";

// Interface para o documento vindo do backend Python
interface DocumentoBackend {
  id: number; // ID único do banco (Primary Key)
  arquivo: string;
  qualidade: string;
  categoria: string;
  dados_extraidos: any;
}

// Interface estendida para uso no componente
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
  
  // Estados para o Modal de Edição
  const [editingDoc, setEditingDoc] = useState<DocumentoBackend | null>(null);
  const [editFormData, setEditFormData] = useState<Record<string, string>>({});
  const [savingData, setSavingData] = useState(false);

  const [reenviando, setReenviando] = useState<string | null>(null);
  
  const { showToast } = useToast(); // Hook de notificação

  const fetchResultados = useCallback(async () => {
    // Permite buscar mesmo sem candidatoId estrito para facilitar testes (fallback)
    setLoading(true);

    try {
        // 1. Busca dados do Python (Backend Local)
        // Usa 'teste' como fallback se candidatoId for nulo
        const res = await fetch(`http://localhost:5003/candidato/${candidatoId || 'teste'}/todos_documentos`);
        let docsBackend: DocumentoBackend[] = [];
        
        if (res.ok) {
            const json = await res.json();
            docsBackend = json.documentos || [];
        } else {
             console.warn("Falha ao buscar documentos do backend.");
        }

        // 2. Processa os documentos para exibição
        const docsProcessados = docsBackend.map((doc) => {
            // Tenta pegar URL do supabase se existir (opcional, pois removemos o botão visualizar)
            // const { data } = supabase.storage.from("documents").getPublicUrl(`candidato_${candidatoId}/${doc.arquivo}`);
            
            return {
                ...doc,
                // publicUrl: data.publicUrl, 
                // Define status baseado na qualidade ('Aprovado' = aceito)
                status: doc.qualidade.includes("Aprovado") ? "aceito" : "recusado",
                motivoRecusa: doc.qualidade.includes("Aprovado") ? "" : doc.qualidade
            } as FileEntry;
        });

        setDocumentos(docsProcessados);

    } catch (e) {
        console.error("Erro crítico ao buscar documentos:", e);
        showToast("Erro ao carregar documentos.", "error");
    } finally {
        setLoading(false);
    }
  }, [candidatoId, showToast]);

  useEffect(() => {
    fetchResultados();
  }, [fetchResultados]);

  // --- FUNÇÕES DE EDIÇÃO ---
  const openEditModal = (doc: DocumentoBackend) => {
    if (!doc.dados_extraidos) {
        showToast("Não há dados extraídos para este documento.", "info");
        return;
    }
    setEditingDoc(doc);
    
    // Parser seguro para garantir que temos um objeto editável
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
        // Envia o 'documento_id' para o backend atualizar o registro correto
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
            fetchResultados(); // Recarrega a lista para refletir a mudança
        } else {
            showToast(`Erro ao salvar: ${json.erro || "Desconhecido"}`, "error");
        }
    } catch (e) { 
        showToast("Erro de conexão com o servidor.", "error");
    }
    setSavingData(false);
  };

  // --- FUNÇÃO DE REENVIO ---
  const handleReenvio = (arquivo: string, file: File) => {
    if (!candidatoId) return;
    setReenviando(arquivo);
    
    const formData = new FormData();
    // Envia o arquivo com o nome original para substituir o antigo
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
            // Opcional: Remover da lista visualmente enquanto processa
            // setDocumentos((prev) => prev.filter((d) => d.arquivo !== arquivo));
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
      
      {loading ? (
        <div className="loading-container">
             <div className="spinner"></div> 
             <p>Carregando resultados...</p>
        </div>
      ) : (
        <div className="document-list">
          
          {/* --- MODAL DE EDIÇÃO (COM NOVO VISUAL) --- */}
          {editingDoc && (
            <div className="modal-overlay">
                <div className="edit-modal">
                    <div className="modal-header">
                        <h3>Dados Extraídos: {editingDoc.arquivo}</h3>
                        <button className="close-btn" onClick={() => setEditingDoc(null)}>×</button>
                    </div>
                    
                    <div className="modal-body">
                        <div className="info-text">
                            Confirme se os dados abaixo conferem com o documento original. 
                            Você pode corrigir qualquer erro encontrado.
                        </div>
                        
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
                    
                    <div className="modal-footer">
                        <button className="cancel-btn" onClick={() => setEditingDoc(null)}>
                            Cancelar
                        </button>
                        <button 
                            className="save-btn" 
                            onClick={saveEditedData} 
                            disabled={savingData}
                        >
                            {savingData ? "Salvando..." : "Confirmar Alterações"}
                        </button>
                    </div>
                </div>
            </div>
          )}

          {/* --- LISTA DE DOCUMENTOS --- */}
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
                            <div className="justificativa">
                                Motivo: {doc.motivoRecusa}
                            </div>
                        ) : (
                            <div className="categoria-info">
                                Tipo: <strong>{doc.categoria}</strong>
                            </div>
                        )}
                    </div>

                    <div className="document-actions">
                        {/* Botão Conferir Dados (Aparece para Aceitos com dados) */}
                        {doc.dados_extraidos && doc.status === 'aceito' && (
                            <button className="conferir-btn" onClick={() => openEditModal(doc)}>
                                Conferir Dados
                            </button>
                        )}

                        {/* Botão de Reenvio (Apenas para Recusados) */}
                        {doc.status === 'recusado' && (
                             <label className="reenvio-label">
                                {reenviando === doc.arquivo ? "Enviando..." : "Corrigir / Reenviar"}
                                <input 
                                    type="file" 
                                    hidden 
                                    accept="image/*,.pdf"
                                    onChange={e => e.target.files?.[0] && handleReenvio(doc.arquivo, e.target.files[0])} 
                                    disabled={!!reenviando} 
                                />
                            </label>
                        )}

                        <span className={`badge badge-${doc.status}`}>
                            {doc.status === 'aceito' ? 'Aprovado' : 'Atenção'}
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