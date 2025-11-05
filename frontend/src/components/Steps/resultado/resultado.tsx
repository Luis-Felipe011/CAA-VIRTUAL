import { useEffect, useState, useCallback } from "react";
import { supabase } from "../../../supabaseClient";
import "./resultado.scss";

// Interface para o ficheiro vindo do Supabase Storage
interface FileEntry {
  fileName: string;
  publicUrl: string;
  // Status vindo do nosso backend
  status?: "aceito" | "recusado"; 
  motivoRecusa?: string;
}

interface ResultadoProps {
  candidatoId: string;
  batchId: string | null; // batchId não é usado aqui, mas mantido por consistência
}

// Interface para o documento reprovado vindo do nosso backend
interface DocumentoReprovado {
  arquivo: string;       // Este é o 'fileName'
  qualidade: string;     // Este é o 'motivoRecusa'
  categoria: string;
  dados_extraidos: any;
}

const Resultado: React.FC<ResultadoProps> = ({ candidatoId }) => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [reenviando, setReenviando] = useState<string | null>(null);

  const fetchFilesAndStatus = useCallback(async () => {
    if (!candidatoId) return;

    setLoading(true);
    
    // 1. Busca ficheiros do Supabase Storage (para ter a publicUrl)
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

    // 2. Busca status de 'aceito'/'recusado' do Supabase (do funcionário)
    // Assumindo que a tabela de status do funcionário é 'document_status'
    const { data: statusData } = await supabase
      .from('document_status') 
      .select('file_path, status, justificativa')
      .eq('candidato_id', candidatoId);

    const statusMap = new Map<string, { status: "aceito" | "recusado", motivo: string }>();
    if (statusData) {
      for (const row of statusData) {
        // Garante que o status seja tratado como o tipo literal esperado
        statusMap.set(row.file_path, { status: row.status as "aceito" | "recusado", motivo: row.justificativa || "" });
      }
    }
    
    // 3. Busca status de 'reprovado' do analyzer (reprovados pelo sistema)
    let reprovadosDoBackend: DocumentoReprovado[] = []; // <-- Variável local
    try {
        const reprovadosRes = await fetch(`http://localhost:5003/documentos_reprovados?candidato_id=${candidatoId}`);
        if (reprovadosRes.ok) {
            const dataReprovados = await reprovadosRes.json();
            reprovadosDoBackend = dataReprovados.reprovados || []; // <-- Salva aqui
        }
    } catch (e) {
        console.error("Falha ao buscar documentos reprovados pela API", e);
    }

    // 4. Combina os dados
    const filesWithStatus = allFiles.map(f => {
      // 4.1. Verifica se o funcionário já deu um status (Aceito/Recusado)
      const dbStatus = statusMap.get(f.publicUrl);
      if (dbStatus) {
        return {
          ...f,
          status: dbStatus.status,
          motivoRecusa: dbStatus.motivo
        };
      }
      
      // 4.2. Se não, verifica se foi reprovado pelo *sistema* (analyzer)
      // --- CORREÇÃO DO BUG AQUI ---
      const reprovadoPeloSistema = reprovadosDoBackend.find(r => r.arquivo === f.fileName);
      if (reprovadoPeloSistema) {
        return {
          ...f,
          status: "recusado",
          motivoRecusa: reprovadoPeloSistema.qualidade // <-- Usando a variável correta
        }
      }
      // --- FIM DA CORREÇÃO ---
      
      // 4.3. Se não, está pendente
      return f; // Sem status (pendente de análise do funcionário)
    });
    setFiles(filesWithStatus as FileEntry[]);
    setLoading(false);
    setLoading(false);
  }, [candidatoId]);

  useEffect(() => {
    fetchFilesAndStatus();
  }, [fetchFilesAndStatus]);

  // Lógica de Reenvio (movida do EmAnaliseReenvio.tsx)
  const handleReenvio = (arquivo: string, file: File) => {
    if (!candidatoId) return;

    setReenviando(arquivo);
    const formData = new FormData();
    // Renomeia o ficheiro de upload para o nome original (importante para o backend)
    formData.append("files", file, arquivo); 
    formData.append("candidato_id", candidatoId);
    
    fetch("http://localhost:5003/processar_documentos", {
      method: "POST",
      body: formData,
    })
    .then(res => res.json())
    .then(data => {
        setReenviando(null);
        if (data.status === "processamento_iniciado") {
            alert("Arquivo reenviado para análise. O status será atualizado em breve.");
            // Remove o item da lista (ele agora está em análise)
            setFiles((prev) => prev.filter((d) => d.fileName !== arquivo));
        } else {
            alert("Erro ao reenviar: " + (data.erro || "Erro desconhecido"));
        }
    })
    .catch(() => {
        setReenviando(null);
        alert("Erro de rede ao reenviar.");
    });
  };

  const aceitos = files.filter(f => f.status === "aceito");
  const rejeitados = files.filter(f => f.status === "recusado");
  const pendentes = files.filter(f => f.status !== "aceito" && f.status !== "recusado");


  return (
    <div className="resultado-container">
      <h2>Resultado da Análise</h2>
      {loading ? (
        <div className="loading">Carregando resultados...</div>
      ) : (
        <div className="document-list">
          
          {/* SEÇÃO DOS REJEITADOS (COM REENVIO) */}
          <div className="resultado-bloco">
            <h3>Documentos Rejeitados</h3>
            {rejeitados.length === 0 ? (
              <p className="resultado-vazio">Nenhum documento rejeitado.</p>
            ) : (
              rejeitados.map(f => (
                <div className="document-card resultado-card rejeitado" key={f.fileName}>
                  <div className="document-info">
                    <div className="document-title">
                      <span className="file-icon">📎</span>
                      <span className="doc-name">{f.fileName}</span>
                    </div>
                    {f.motivoRecusa && (
                       <div className="justificativa">
                         Motivo: {f.motivoRecusa}
                       </div>
                    )}
                  </div>
                  <div className="document-actions">
                    {f.publicUrl && (
                        <a
                        href={f.publicUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="file-link"
                        >
                        Visualizar
                        </a>
                    )}
                    <span className="badge badge-rejeitado">Rejeitado</span>
                    
                    {/* Lógica de Reenvio */}
                    <input
                      type="file"
                      accept="image/*,.pdf"
                      id={`reenvio-${f.fileName}`}
                      style={{ display: 'none' }} // Esconde o input
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          handleReenvio(f.fileName, e.target.files[0]);
                        }
                      }}
                      disabled={reenviando === f.fileName}
                    />
                    <label htmlFor={`reenvio-${f.fileName}`} className="button-reenvio">
                       {reenviando === f.fileName ? "Enviando..." : "Reenviar"}
                    </label>
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* SEÇÃO DOS ACEITOS */}
          <div className="resultado-bloco">
            <h3>Documentos Aceitos</h3>
            {aceitos.length === 0 ? (
              <p className="resultado-vazio">Nenhum documento aceito ainda.</p>
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
                    <a
                      href={f.publicUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="file-link"
                    >
                      Visualizar
                    </a>
                    <span className="badge badge-aceito">Aceito</span>
                  </div>
                </div>
              ))
            )}
          </div>
          
           {/* SEÇÃO DOS PENDENTES (se houver) */}
           {pendentes.length > 0 && (
             <div className="resultado-bloco">
                <h3>Documentos Pendentes de Análise</h3>
                {pendentes.map(f => (
                    <div className="document-card" key={f.fileName}>
                        <div className="document-info">
                            <div className="document-title">
                            <span className="file-icon">📎</span>
                            <span className="doc-name">{f.fileName}</span>
                            </div>
                        </div>
                        <div className="document-actions">
                             <a
                                href={f.publicUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="file-link"
                            >
                                Visualizar
                            </a>
                            <span className="badge badge-pendente" style={{background: '#ffc107', color: 'black'}}>Em Análise</span>
                        </div>
                    </div>
                ))}
             </div>
           )}

        </div>
      )}
    </div>
  );
};

export default Resultado;