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
import EmAnalise from '../../../components/Steps/analise/analise' // ATENÇÃO: Importe o analise.tsx, não o Reenvio
import Resultado from '../../../components/Steps/resultado/resultado'

export function Home() {
  const [etapaAtual, setEtapaAtual] = useState(1)
  const [candidatoId, setCandidatoId] = useState<string | null>(null)
  const [nomeUsuario, setNomeUsuario] = useState('Usuário')
  const [loading, setLoading] = useState(true)
  
  // --- ESTADO CRÍTICO: Guarda o ID do lote atual ---
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
    const { data } = await supabase
      .from('candidate')
      .select('nome, step')
      .eq('id', session.user.id)
      .single()
    
    setCandidatoId(session.user.id)
    
    if (data) {
      setNomeUsuario(data.nome || 'Usuário')
      // Se já estava no passo 4 ou 5, mantém, senão começa do 1
      setEtapaAtual(typeof data.step === "number" ? data.step : 1)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    autenticarECarregarCandidato()
  }, [autenticarECarregarCandidato])

  // Função chamada quando o upload termina
  const handleProcessamentoIniciado = (novoBatchId: string) => {
    console.log("Processamento iniciado com Batch ID:", novoBatchId);
    setBatchId(novoBatchId); 
    setEtapaAtual(4); // Vai para a tela de análise
  };

  // Função chamada quando a análise termina
  const handleAnaliseConcluida = () => {
    console.log("Análise concluída!");
    setEtapaAtual(5); // Vai para o resultado
  };

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
      // Passo 3: Upload
      return <DocumentProcessor 
                candidatoId={candidatoId} 
                onProcessamentoIniciado={handleProcessamentoIniciado} 
             />
    } else if (etapaAtual === 4) {
      // Passo 4: Polling (Análise)
      return <EmAnalise 
                batchId={batchId} 
                onAnaliseConcluida={handleAnaliseConcluida} 
             />
    } else {
      // Passo 5: Resultado
      return <Resultado 
                candidatoId={candidatoId ?? ''} 
                batchId={batchId}
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