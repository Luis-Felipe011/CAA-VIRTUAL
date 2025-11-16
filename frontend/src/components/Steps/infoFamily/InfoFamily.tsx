import { useState, useEffect } from "react";
import { supabase } from "../../../supabaseClient";
import Input from "../../Input/Input";
import Button from "../../Button/Button";
import "./InfoFamily.scss";
import { useToast } from "../../../context/ToastContext"; // <--- Importar

interface Familiar {
  id: string;
  name: string;
  cpf: string;
}

interface Props {
  candidatoId: string;
  onStepChange?: (novoStep: number) => void;
}

export default function InfoFamily({ onStepChange, candidatoId }: Props) {
  const [nomeFamiliar, setNomeFamiliar] = useState("");
  const [cpf, setCpf] = useState("");
  const [loading, setLoading] = useState(false);
  const [familiares, setFamiliares] = useState<Familiar[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const { showToast } = useToast(); // <--- Hook

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setToken(data.session?.access_token ?? null);
    });
  }, []);

  const buscarFamiliares = async () => {
    if (!candidatoId) return;
    try {
        const resposta = await fetch(`http://localhost:5000/api/familiares?candidato_id=${candidatoId}`, {
            headers: { "Authorization": `Bearer ${token}` },
        });
        const json = await resposta.json();
        if (json.success) setFamiliares(json.familiares);
    } catch (e) {
        console.error("Erro ao buscar familiares", e);
    }
  };

  useEffect(() => {
    if (candidatoId) {
      buscarFamiliares();
    }
  }, [candidatoId]);

  async function salvarFamiliar() {
    if (!nomeFamiliar.trim() || !cpf.trim()) {
      showToast("Preencha nome e CPF do familiar.");
      return;
    }
    setLoading(true);
    try {
      const resposta = await fetch("http://localhost:5000/api/familiar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: nomeFamiliar,
          cpf,
          candidato_id: candidatoId,
        }),
      });

      const json = await resposta.json();

      if (json.success) {
        setNomeFamiliar("");
        setCpf("");
        buscarFamiliares(); 
        showToast("Membro familiar adicionado!", "success");
      } else {
        showToast("Erro ao salvar: " + json.error, "error");
      }
    } catch (error) {
      console.error(error);
      showToast("Erro de conexão.", "error");
    }
    setLoading(false);
  }

  return (
    <div className="infoFamily-form">
      <h2>Adicionar membro familiar</h2>
      <div className="form-fields">
        <Input
          placeholder="Nome completo do Membro familiar"
          value={nomeFamiliar}
          onChange={setNomeFamiliar}
        />
        <Input
          placeholder="CPF (xxx.xxx.xxx-xx)"
          value={cpf}
          onChange={setCpf}
        />
      </div>
      <Button
        text={loading ? "Salvando..." : "Confirmar membro"}
        onClick={salvarFamiliar}
      />

     <div className="familiares-list">
        <h3>Membros familiares adicionados</h3>
        {familiares.length === 0 ? (
          <p>Nenhum membro familiar adicionado ainda.</p>
        ) : (
          <ul>
            {familiares.map(f => (
              <li key={f.id}>
                <span className="nome">{f.name}</span>
                <span className="cpf">{f.cpf}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="confirmar-nucleo-btn">
        <Button
          text="Confirmar núcleo familiar e Avançar"
          color="primary" // Destaca o botão de avançar
          onClick={async () => {
            setLoading(true);
            try {
              const resposta = await fetch("http://localhost:5000/api/candidato/step", {
                method: "PATCH",
                headers: {
                  "Content-Type": "application/json",
                  "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ step: 3, candidato_id: candidatoId }),
              });
              const json = await resposta.json();
              if (json.success) {
                showToast("Núcleo familiar confirmado!", "success");
                if (onStepChange) onStepChange(3);
              } else {
                showToast("Erro ao avançar etapa: " + json.error, "error");
              }
            } catch (error) {
              showToast("Erro ao avançar etapa.", "error");
            }
            setLoading(false);
          }}
        />
      </div>
    </div>
  );
}