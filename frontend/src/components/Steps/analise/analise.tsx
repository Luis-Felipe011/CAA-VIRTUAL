import React, { useEffect, useState } from "react";
import "./analise.scss";

interface Props {
  batchId: string | null;
  onAnaliseConcluida: () => void;
}

const EmAnalise: React.FC<Props> = ({ batchId, onAnaliseConcluida }) => {
  const [statusMessage, setStatusMessage] = useState(
    "Seus documentos e informações estão sendo analisados pela equipe."
  );

  useEffect(() => {
    // Se não houver batchId, algo correu mal no passo anterior
    if (!batchId) {
      setStatusMessage("Aguardando envio dos documentos...");
      return;
    }

    // Inicia o "polling" (pergunta ao backend a cada 5 segundos)
    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:5003/resultado_lote/${batchId}`);
        
        if (response.ok) {
            const data = await response.json();

            if (data.status === "concluido") {
            // --- SUCESSO: A ANÁLISE TERMINOU ---
            setStatusMessage("Análise concluída! Avançando para os resultados...");
            clearInterval(intervalId); // Para de perguntar
            
            // Espera 1.5s só para o usuário ler a mensagem e avança
            setTimeout(() => {
                onAnaliseConcluida(); 
            }, 1500);
            } else if (data.status === "processando") {
                setStatusMessage("Análise em andamento... aguarde.");
            }
        }
      } catch (error) {
        console.error("Erro ao verificar status:", error);
      }
    }, 5000); // 5000ms = 5 segundos

    // Limpa o intervalo se o usuário sair da tela
    return () => clearInterval(intervalId);
    
  }, [batchId, onAnaliseConcluida]);

  return (
    <div className="em-analise-container">
      <h2>Em Análise</h2>
      <p>{statusMessage}</p>
      <div className="analise-loader"></div>
    </div>
  );
};

export default EmAnalise;