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
    if (!batchId) {
      setStatusMessage("Erro: ID do lote não encontrado. Tente novamente.");
      return;
    }

    // Inicia o "polling" (sondagem)
    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:5003/resultado_lote/${batchId}`);
        const data = await response.json();

        if (response.status === 500) {
           throw new Error(data.erro || "Erro de servidor");
        }

        if (data.status === "concluido") {
          // --- SUCESSO ---
          setStatusMessage("Análise concluída! Avançando para os resultados...");
          clearInterval(intervalId); // Para o polling
          setTimeout(() => {
            onAnaliseConcluida(); // Chama a função do home.tsx para ir para a Etapa 5
          }, 1500); // Espera 1.5s para o usuário ler a mensagem
        } else if (data.status === "processando") {
          // Ainda está processando, continua...
          setStatusMessage("Análise em andamento... aguarde.");
        } else {
          // Status 'nao_encontrado' ou outro
          setStatusMessage("Aguardando o início do processamento...");
        }

      } catch (error: any) {
        console.error("Erro no polling:", error);
        setStatusMessage(`Erro ao verificar status: ${error.message}. Tentando novamente...`);
      }
    }, 5000); // Pergunta ao backend a cada 5 segundos

    // Limpa o intervalo se o componente for desmontado
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