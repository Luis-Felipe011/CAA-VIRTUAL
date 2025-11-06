import React, { useEffect, useState } from "react";
import DadosExtraidosModal from "./DadosExtraidosModal";
import './DadosExtraidosModal.scss';

interface Props {
  candidatoId?: string | null;
  onReenviar?: (arquivos: string[]) => void;
}

const ResultadoAprovado: React.FC<Props> = ({ candidatoId, onReenviar }) => {
  const [reprovados, setReprovados] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dadosExtraidos, setDadosExtraidos] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (!candidatoId) return;
    fetch(`http://localhost:5003/documentos_reprovados?candidato_id=${candidatoId}`)
      .then((res) => res.json())
      .then((data) => {
        setReprovados(data.reprovados || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [candidatoId]);


  useEffect(() => {
    if (!candidatoId || reprovados.length > 0) return;
    // Buscar dados extraídos dos documentos aprovados
    fetch(`http://localhost:5003/dados_extraidos_aprovados?candidato_id=${candidatoId}`)
      .then((res) => res.json())
      .then((data) => {
        setDadosExtraidos(data.aprovados || []);
      });
  }, [candidatoId, reprovados]);

  if (loading) return <div>Carregando resultado...</div>;

  if (reprovados.length === 0) {
    return (
      <div className="resultado-aprovado">
        <h2>Parabéns!</h2>
        <p>Todos os seus documentos foram aprovados. Aguarde o próximo contato da equipe.</p>
        {dadosExtraidos.length > 0 && (
          <button onClick={() => setModalOpen(true)} style={{marginTop: 16}}>
            Ver dados extraídos
          </button>
        )}
        <DadosExtraidosModal open={modalOpen} onClose={() => setModalOpen(false)} dados={dadosExtraidos} />
      </div>
    );
  }

  // Se houver reprovados, mostra lista e botão para reenviar
  return (
    <div className="resultado-reprovado">
      <h2>Documentos pendentes</h2>
      <p>Os documentos abaixo precisam ser reenviados:</p>
      <ul>
        {reprovados.map((doc) => (
          <li key={doc.arquivo}>
            <strong>{doc.arquivo}</strong> - {doc.qualidade}
          </li>
        ))}
      </ul>
      <button
        onClick={() => {
          if (onReenviar) onReenviar(reprovados.map((d) => d.arquivo));
        }}
        style={{ marginTop: 16 }}
      >
        Reenviar documentos
      </button>
    </div>
  );
};

export default ResultadoAprovado;
