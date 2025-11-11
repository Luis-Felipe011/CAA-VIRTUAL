import React, { useEffect, useState } from "react";
import Button from "../../Button/Button";
import "./analise.scss";

interface DocumentoReprovado {
  arquivo: string;
  qualidade: string;
  categoria: string;
  dados_extraidos: any;
}

interface Props {
  candidatoId?: string | null;
}

const EmAnalise: React.FC<Props> = ({ candidatoId }) => {
  const [reprovados, setReprovados] = useState<DocumentoReprovado[]>([]);
  const [reenviando, setReenviando] = useState<string | null>(null);

  useEffect(() => {
    if (!candidatoId) return;
    fetch(`http://localhost:5003/documentos_reprovados?candidato_id=${candidatoId}`)
      .then((res) => res.json())
      .then((data) => setReprovados(data.reprovados || []));
  }, [candidatoId]);

  const handleReenvio = (arquivo: string, file: File) => {
    setReenviando(arquivo);
    const formData = new FormData();
    formData.append("files", file);
    if (candidatoId) formData.append("candidato_id", candidatoId);
    fetch("http://localhost:5003/processar_documentos", {
      method: "POST",
      body: formData,
    })
      .then(() => {
        setReenviando(null);
        setReprovados((prev) => prev.filter((d) => d.arquivo !== arquivo));
      })
      .catch(() => setReenviando(null));
  };

  return (
    <div className="em-analise-container">
      <h2>Em Análise</h2>
      <p>
        Seus documentos e informações estão sendo analisados pela equipe.<br />
        Você receberá uma notificação assim que o processo for concluído.
      </p>
      <div className="analise-loader"></div>
      {/* Reenvio removido. O reenvio de documentos reprovados aparece apenas na aba de resultado. */}
    </div>
  );
};

export default EmAnalise;
