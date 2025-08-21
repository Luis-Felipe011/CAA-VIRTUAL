import { useEffect, useState } from "react"
import { supabase } from "../../../../../frontend/src/supabaseClient"
import Modal, { ModalHandle } from "../../Modal/Modal"
import Input from "../../Input/Input"
import Button from "../../Button/Button"
import familypng from "../../../assets/img/family.png"
import "./Infocandidate.scss"

interface Props {
  setCandidatoId: (id: string) => void
  candidatoId: string | null
  onStepChange?: (novoStep: number) => void; // Adicione a prop opcional
}

export default function InfoCandidate({ onStepChange, setCandidatoId }: Props) {
  const [nomeCandidato, setNomeCandidato] = useState("")
  const [cpf, setCpf] = useState("")
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    // Busca o token JWT do usuário logado
    supabase.auth.getSession().then(({ data }) => {
      setToken(data.session?.access_token ?? null)
    })
  }, [])

  async function salvarCandidato() {
    if (!nomeCandidato.trim() || !cpf.trim()) {
      alert("Preencha todos os campos.")
      return
    }
    setLoading(true)
    try {
      const resposta = await fetch("http://localhost:5000/candidato", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ nome: nomeCandidato, cpf, step: 2 })
      })

      const json = await resposta.json()

      if (json.success) {
        setCandidatoId(json.id);
        alert("Candidato salvo com sucesso!");
        if (onStepChange) onStepChange(2); 
      } else {
        alert("Erro ao salvar candidato: " + json.error);
      }

      if (json.success) {
        setCandidatoId(json.id)
      } else {
        alert("Erro ao salvar candidato: " + json.error)
      }
    } catch (error) {
      console.error(error)
      alert("Erro ao salvar candidato.")
    }
    setLoading(false)
  }

  return (
    <>
    
        <div className="infocandidate-form">
          <h2>Dados do candidato</h2>
          <div className="form-fields">
            <Input placeholder="Nome completo do candidato" value={nomeCandidato} onChange={setNomeCandidato} />
            <Input placeholder="CPF (xxx.xxx.xxx-xx)" value={cpf} onChange={setCpf} />
          </div>
          <Button text={loading ? "Salvando..." : "Confirmar candidato"} onClick={salvarCandidato} />
        </div>
      
    </>
  )
}