import { forwardRef, useImperativeHandle, useState } from "react"
import "./Modal.scss"
import Input from "../Input/Input"
import Button from "../Button/Button"
import { useToast } from "../../context/ToastContext" // <--- Importar

export interface ModalHandle {
  abrir: () => void
  fechar: () => void
}

interface ModalProps {
  candidatoId: string
}

const Modal = forwardRef<ModalHandle, ModalProps>(({ candidatoId }, ref) => {
  const [aberto, setAberto] = useState(false)
  const [nome, setNome] = useState("")
  const { showToast } = useToast() // <--- Hook

  useImperativeHandle(ref, () => ({
    abrir: () => setAberto(true),
    fechar: () => setAberto(false),
  }))

  async function setFamilyDatabase() {
    if (!nome.trim()) {
      showToast("Digite um nome válido.")
      return
    }

    try {
      const resposta = await fetch("http://localhost:5000/familia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: nome, candidato_id: candidatoId })
      })

      const json = await resposta.json()

      if (json.success) {
        showToast("Familiar salvo com sucesso!", "success")
        setNome("")
        setAberto(false)
      } else {
        showToast("Erro: " + json.error, "error")
      }
    } catch (error) {
      console.error("Erro ao salvar:", error)
      showToast("Erro ao salvar familiar.", "error")
    }
  }

  if (!aberto) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Adicionar membro</h2>
          <button
            className="modal-close"
            aria-label="Fechar modal"
            onClick={() => setAberto(false)}
            type="button"
          >
            ×
          </button>
        </div>

        <div className="form-group">
          <Input
            className="custom-input"
            placeholder="Nome do candidato ou familiar"
            value={nome}
            onChange={setNome}
          />
          <Button text="Adicionar" onClick={setFamilyDatabase} />
        </div>
      </div>
    </div>
  )
})

export default Modal