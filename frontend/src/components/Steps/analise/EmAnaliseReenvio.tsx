
import React, { useEffect } from "react";
import "./analise.scss";

interface Props {
  candidatoId?: string | null;
}

const EmAnalise: React.FC<Props> = () => {
  useEffect(() => {
    // Aqui pode-se simular um tempo de análise, ou aguardar evento do backend
    // O avanço de etapa é controlado pelo Home.tsx via evento analiseFinalizada
  }, []);

  return (
    <div className="em-analise-container">
      <h2>Em Análise</h2>
      <p>
        Seus documentos e informações estão sendo analisados pela equipe.<br />
        Você receberá uma notificação assim que o processo for concluído.
      </p>
      <div className="analise-loader"></div>
    </div>
  );
};

export default EmAnalise;
