import { useState, useEffect } from "react";
import { supabase } from "../../../supabaseClient";
import Input from "../../Input/Input";
import Button from "../../Button/Button";
import "./InfoFamily.scss";

interface Familiar {
  id: string;
  name: string;
  cpf: string;
}

interface Props {
  candidatoId: string;
   onStepChange?: (novoStep: number) => void; // Adicione a prop opcional
}

export default function InfoFamily({ onStepChange, candidatoId }: Props) {
  const [nomeFamiliar, setNomeFamiliar] = useState("");
  const [cpf, setCpf] = useState("");
  const [loading, setLoading] = useState(false);
  const [familiares, setFamiliares] = useState<Familiar[]>([]);
  const [token, setToken] = useState<string | null>(null);

  // Busca o token ao montar
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setToken(data.session?.access_token ?? null);
    });
  }, []);

  // Função para buscar familiares
  const buscarFamiliares = async () => {
    if (!candidatoId) return;
    const { data } = await supabase
      .from("family")
      .select("id, name, cpf")
      .eq("candidato_id", candidatoId);
    if (data) setFamiliares(data as Familiar[]);
  };

  useEffect(() => {
    if (candidatoId) {
      buscarFamiliares();
    }
  }, [candidatoId]);

  async function salvarFamiliar() {
    if (!nomeFamiliar.trim() || !cpf.trim()) {
      alert("Preencha todos os campos.");
      return;
    }
    setLoading(true);
    try {
      const resposta = await fetch("http://localhost:5000/familiar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          nome: nomeFamiliar,
          cpf,
          candidato_id: candidatoId,
        }),
      });

      const json = await resposta.json();

      if (json.success) {
        setNomeFamiliar("");
        setCpf("");
        buscarFamiliares(); 
        alert("Familiar salvo com sucesso!");
      } else {
        alert("Erro ao salvar familiar: " + json.error);
      }
    } catch (error) {
      console.error(error);
      alert("Erro ao salvar familiar.");
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
          text="Confirmar núcleo familiar"
          onClick={async () => {
            setLoading(true);
            try {
              const resposta = await fetch("http://localhost:5000/candidato/step", {
                method: "PATCH",
                headers: {
                  "Content-Type": "application/json",
                  "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ step: 3 }),
              });
              const json = await resposta.json();
              if (json.success) {
                alert("Núcleo familiar confirmado! Avançando para próxima etapa.");
                 if (onStepChange) onStepChange(3); // Atualiza o step na Home
              } else {
                alert("Erro ao avançar etapa: " + json.error);
              }
            } catch (error) {
              alert("Erro ao avançar etapa.");
            }
            setLoading(false);
          }}
        />
      </div>
    </div>
  );
}