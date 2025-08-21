import { useEffect, useState } from "react";
import { supabase } from "../../../supabaseClient";
import "./resultado.scss";

interface FileEntry {
  fileName: string;
  publicUrl: string;
  status?: string;
}

interface ResultadoProps {
  candidatoId: string;
}

const Resultado: React.FC<ResultadoProps> = ({ candidatoId }) => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFilesAndStatus = async () => {
      setLoading(true);
      // Busca arquivos do storage
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
      // Busca status dos arquivos
      const res = await fetch(`http://localhost:5000/documento/status?candidato_id=${candidatoId}`);
      let statusObj: { [key: string]: string | undefined } = {};
      if (res.ok) statusObj = await res.json();
      const filesWithStatus = allFiles.map(f => ({
        ...f,
        status: statusObj[f.publicUrl] // 'aceito', 'recusado' ou undefined
      }));
      setFiles(filesWithStatus);
      setLoading(false);
    };
    if (candidatoId) fetchFilesAndStatus();
  }, [candidatoId]);

  const aceitos = files.filter(f => f.status === "aceito");
  const rejeitados = files.filter(f => f.status === "recusado");

  return (
    <div className="resultado-container">
      <h2>Resultado da Análise</h2>
      {loading ? (
        <div className="loading">Carregando arquivos...</div>
      ) : (
        <div className="document-list">
          <div className="resultado-bloco">
            <h3>Documentos Aceitos</h3>
            {aceitos.length === 0 ? (
              <p className="resultado-vazio">Nenhum documento aceito.</p>
            ) : (
              aceitos.map(f => (
                <div className="document-card resultado-card aceito" key={f.publicUrl}>
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
          <div className="resultado-bloco">
            <h3>Documentos Rejeitados</h3>
            {rejeitados.length === 0 ? (
              <p className="resultado-vazio">Nenhum documento rejeitado.</p>
            ) : (
              rejeitados.map(f => (
                <div className="document-card resultado-card rejeitado" key={f.publicUrl}>
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
                    <span className="badge badge-rejeitado">Rejeitado</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Resultado;