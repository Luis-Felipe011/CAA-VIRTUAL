import { useEffect, useState } from "react"
import { supabase } from "../../../supabaseClient"
import Input from "../../Input/Input"
import Button from "../../Button/Button"
import "./Infocandidate.scss"
import { useToast } from "../../../context/ToastContext" // <--- Importar

interface Props {
  setCandidatoId: (id: string) => void
  candidatoId: string | null
  onStepChange?: (novoStep: number) => void;
}

export default function InfoCandidate({ onStepChange, setCandidatoId }: Props) {
  const [nomeCandidato, setNomeCandidato] = useState("")
  const [cpf, setCpf] = useState("")
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const { showToast } = useToast() // <--- Hook

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setToken(data.session?.access_token ?? null)
    })
  }, [])

  async function salvarCandidato() {
    if (!nomeCandidato.trim() || !cpf.trim()) {
      showToast("Preencha todos os campos.") // UX melhorada
      return
    }
    setLoading(true)
    try {
      const resposta = await fetch("http://localhost:5000/api/candidato", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ name: nomeCandidato, cpf, step: 2 })
      })

      const json = await resposta.json()

      if (json.success) {
        setCandidatoId(json.id);
        showToast("Dados salvos com sucesso!", "success") // Feedback positivo
        if (onStepChange) onStepChange(2); 
      } else {
        showToast("Erro ao salvar: " + json.error, "error")
      }

    } catch (error) {
      console.error(error)
      showToast("Erro de conexão ao salvar candidato.", "error")
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