import React from "react";
import "./analise.scss";

const EmAnalise: React.FC = () => {
  return (
    <div className="em-analise-container">
      <h2>Em Análise</h2>
      <p>
        Seus documentos e informações estão sendo analisados pela equipe. 
        Você receberá uma notificação assim que o processo for concluído.
      </p>
      <div className="analise-loader"></div>
    </div>
  );
};

export default EmAnalise;