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
import EmAnalise from '../../../components/Steps/analise/analise' 
import Resultado from '../../../components/Steps/resultado/resultado'

export function Home() {
  const [etapaAtual, setEtapaAtual] = useState(1)
  const [candidatoId, setCandidatoId] = useState<string | null>(null)
  const [nomeUsuario, setNomeUsuario] = useState('Carregando...')
  const [loading, setLoading] = useState(true)
  const [batchId, setBatchId] = useState<string | null>(null)

  const handleStepChange = (novoStep: number) => {
    setEtapaAtual(novoStep);
  };

  const autenticarECarregarCandidato = useCallback(async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session || !session.user) {
      window.location.href = "/"
      return
    }
    
    const userId = session.user.id;
    setCandidatoId(userId);

    const { data } = await supabase
      .from('candidate')
      .select('nome, step')
      .eq('id', userId)
      .maybeSingle()
    
    const emailName = session.user.email?.split('@')[0] || 'Usuário';
    
    if (data) {
      setNomeUsuario(data.nome || emailName)
      if (data.step && typeof data.step === 'number' && data.step > 0) {
          setEtapaAtual(data.step)
      }
    } else {
      setNomeUsuario(emailName)
      setEtapaAtual(1)
    }
    
    setLoading(false)
  }, [])

  useEffect(() => {
    autenticarECarregarCandidato()
  }, [autenticarECarregarCandidato])

  const handleProcessamentoIniciado = (novoBatchId: string) => {
    console.log("Novo Batch iniciado:", novoBatchId);
    setBatchId(novoBatchId); 
    setEtapaAtual(4); // Vai para Análise
  };

  const handleAnaliseConcluida = () => {
    console.log("Análise concluída.");
    setEtapaAtual(5); // Vai para Resultado
  };

  // --- NOVA FUNÇÃO: Chamada quando o usuário reenvia um documento ---
  const handleReenvioIniciado = (novoBatchId: string) => {
     console.log("Reenvio iniciado. Voltando para análise...", novoBatchId);
     setBatchId(novoBatchId); // Atualiza com o ID do novo processamento
     setEtapaAtual(4); // Volta para a tela de loading/polling
  }

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
      return <DocumentProcessor 
                candidatoId={candidatoId} 
                onProcessamentoIniciado={handleProcessamentoIniciado} 
             />
    } else if (etapaAtual === 4) {
      return <EmAnalise 
                batchId={batchId} 
                onAnaliseConcluida={handleAnaliseConcluida} 
             />
    } else {
      return <Resultado 
                candidatoId={candidatoId ?? ''} 
                batchId={batchId}
                onReenvio={handleReenvioIniciado} // <--- Passamos a função aqui
             />
    }
  }

  if (loading) return <div className="loading">Carregando...</div>

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