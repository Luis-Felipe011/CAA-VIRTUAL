import { useState } from "react"
import "./StepsVertical.scss"
import Button from "../Button/Button";

const etapas = [
    { id: 1, nome: "Adicionar familiares" },
    { id: 2, nome: "Envio de Documentos" },
    { id: 3, nome: "Análise" },
    { id: 4, nome: "Resultado" },
]

interface StepsVerticalProps {
    etapaAtual: number;
  }
  
  export default function StepsVertical({ etapaAtual }: StepsVerticalProps) {
    const etapas = [
      { id: 1, nome: "Adicionar dados do candidato" },
      { id: 2, nome: "Adicionar familiares" },
      { id: 3, nome: "Envio de Documentos" },
      { id: 4, nome: "Análise" },
      { id: 5, nome: "Resultado" },
    ];

  
    const getIcon = (id: number) => {
      if (id < etapaAtual) return "✅";
      if (id === etapaAtual) return "🔄";
      return "⚪";
    };
  
    return (
      <div className="steps-container">
        <ol className="steps-list">
          {etapas.map((etapa) => (
            <li key={etapa.id} className="step-item">
              <div className="step-icon">{getIcon(etapa.id)}</div>
              <div className={`step-text ${etapa.id === etapaAtual ? "active-text" : ""}`}>
                {etapa.nome}
              </div>
            </li>
          ))}
        </ol>
      </div>
    );
  }