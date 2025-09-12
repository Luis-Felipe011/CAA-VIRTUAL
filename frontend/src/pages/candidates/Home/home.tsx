import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../../../supabaseClient'
import UserMenu from '../../../components/User-menu/User-menu'
import './home.scss'
import logo from '../../../assets/svg/logo.svg'
import gradientSvg from '../../../assets/svg/gradient.svg'
import StepsVertical from '../../../components/StepsVertical/StepsVertical'
import Chatbot from '../../../components/Chatbot/Chatbot'
import InfoCandidate from '../../../components/Steps/InfoCandidate/Infocandidate'
import InfoFamily from '../../../components/Steps/infoFamily/InfoFamily'
import UploadTable from '../../../components/Steps/Upload-table/Upload-table'
import EmAnalise from '../../../components/Steps/analise/analise'
import Resultado from '../../../components/Steps/resultado/resultado'

export function Home() {
  const [documents, setDocuments] = useState<any[]>([])
  const [etapaAtual, setEtapaAtual] = useState(1)
  const [candidatoId, setCandidatoId] = useState<string | null>(null)
  const [nomeUsuario, setNomeUsuario] = useState('Usuário')
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState<string | null>(null)

  const handleStepChange = (novoStep: number) => {
    setEtapaAtual(novoStep);
  };

  // Função para autenticação e carregamento do candidato
  const autenticarECarregarCandidato = useCallback(async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session || !session.user) {
      window.location.href = "/"
      return
    }
    setToken(session.access_token)
    const { data } = await supabase
      .from('candidate')
      .select('nome, step')
      .eq('id', session.user.id)
      .single()
    setCandidatoId(session.user.id)
    if (data) {
      setNomeUsuario(data.nome || session.user.email?.split('@')[0] || 'Usuário')
      setEtapaAtual(typeof data.step === "number" ? data.step : 1)
    } else {
      setNomeUsuario(session.user.email?.split('@')[0] || 'Usuário')
      setEtapaAtual(1)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    autenticarECarregarCandidato()
  }, [autenticarECarregarCandidato])

  useEffect(() => {
    if (!token) return
    async function fetchChecklist() {
      try {
        const resposta = await fetch("http://localhost:5000/checklist", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          }
        })
        const json = await resposta.json()
        if (json.checklist && Array.isArray(json.checklist)) {
          const docs = json.checklist.map((item: any[]) => ({
            id: item[0],
            numero: item[1],
            nome: item[2],
            categoria: item[3]
          }))
          setDocuments(docs)
        }
      } catch (error) {
        console.error(error)
      }
    }
    fetchChecklist()
  }, [token])


  function renderEtapa() {
    if (etapaAtual === 1) {
      return <InfoCandidate
        candidatoId={candidatoId}
        setCandidatoId={setCandidatoId}
        onStepChange={handleStepChange}
      />
    } else if (etapaAtual === 2) {
      return <InfoFamily onStepChange={handleStepChange} candidatoId={candidatoId ?? ''} />
    } else if (etapaAtual === 3) {
      return <UploadTable onStepChange={handleStepChange} documents={documents} candidatoId={candidatoId ?? ''} />
    } else if (etapaAtual === 4) {
      return <EmAnalise />
      } else{
        return <Resultado candidatoId={candidatoId ?? ''}/>
      }
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="container">
      <header>
        <img src={logo} alt="Logo" className="logo" />
        <UserMenu
          userName={nomeUsuario}
          userEmail={nomeUsuario + '@exemplo.com'}
          userImage=""
          onLogout={() => supabase.auth.signOut()}
        />
      </header>

      <div className="content">
        <div style={{ padding: '2rem' }}>
          <StepsVertical etapaAtual={etapaAtual} />
        </div>
        <div className="page">{renderEtapa()}</div>
      </div>

      <Chatbot />
    </div>
  )
}