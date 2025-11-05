import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../../../supabaseClient'
import UserMenu from '../../../components/User-menu/User-menu'
import './home.scss'
import logo from '../../../assets/svg/logo.svg'
import StepsVertical from '../../../components/StepsVertical/StepsVertical'
import Chatbot from '../../../components/Chatbot/Chatbot'
import InfoCandidate from '../../../components/Steps/InfoCandidate/Infocandidate'
import InfoFamily from '../../../components/Steps/infoFamily/InfoFamily'
import DocumentProcessor from '../../../components/Steps/DocumentProcessor/DocumentProcessor'
import EmAnalise from '../../../components/Steps/analise/analise' // MUDANÇA: Usando o 'analise.tsx' simples
import Resultado from '../../../components/Steps/resultado/resultado'

export function Home() {
  const [etapaAtual, setEtapaAtual] = useState(1)
  const [candidatoId, setCandidatoId] = useState<string | null>(null)
  const [nomeUsuario, setNomeUsuario] = useState('Usuário')
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState<string | null>(null)

  // --- NOVO ESTADO PARA GUARDAR O ID DO LOTE ---
  const [batchId, setBatchId] = useState<string | null>(null)

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

  // --- NOVA FUNÇÃO ---
  // Chamada pelo DocumentProcessor quando o backend aceita o lote
  const handleProcessamentoIniciado = (novoBatchId: string) => {
    setBatchId(novoBatchId); // Guarda o ID do lote
    setEtapaAtual(4); // Avança para a tela de Análise
  };

  // Esta função é chamada pelo EmAnalise quando o polling termina
  const handleAnaliseConcluida = () => {
    setEtapaAtual(5); // Avança para a tela de Resultado
  };

  // (Removido o useEffect do 'documentosProcessados', pois estamos usando props)

  useEffect(() => {
    if (!token) return
    async function fetchChecklist() {
      try {
        const resposta = await fetch("http://localhost:5000/api/checklist", {
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
      // Passa a nova função 'onProcessamentoIniciado'
      return <DocumentProcessor 
                candidatoId={candidatoId} 
                onProcessamentoIniciado={handleProcessamentoIniciado} 
             />
    } else if (etapaAtual === 4) {
      // Passa o batch_id e a função de callback
      return <EmAnalise 
                batchId={batchId} 
                onAnaliseConcluida={handleAnaliseConcluida} 
             />
    } else {
      // Passa o candidatoId e o batchId (para reenvio)
      return <Resultado 
                candidatoId={candidatoId ?? ''} 
                batchId={batchId}
             />
    }
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="container" style={{ height: '100vh', overflowY: 'auto' }}>
      <header>
        <img src={logo} alt="Logo" className="logo" />
        <UserMenu
          userName={nomeUsuario}
          userEmail={nomeUsuario + '@exemplo.com'}
          userImage=""
          onLogout={() => supabase.auth.signOut()}
        />
      </header>

  <div className="content" style={{ marginLeft: 0 }}>
        <div style={{ padding: '2rem' }}>
          <StepsVertical etapaAtual={etapaAtual} />
        </div>
        <div className="page">{renderEtapa()}</div>
      </div>

      <Chatbot />
    </div>
  )
}