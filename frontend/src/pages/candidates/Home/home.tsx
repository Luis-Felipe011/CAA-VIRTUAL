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
  
  // Estado para o fluxo de documentos
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

    // Busca dados do candidato (tenta ser tolerante a falhas)
    const { data } = await supabase
      .from('candidate')
      .select('nome, step')
      .eq('id', userId)
      .maybeSingle()
    
    // Lógica restaurada (mais robusta)
    const emailName = session.user.email?.split('@')[0] || 'Usuário';
    
    if (data) {
      // Se achou o registro, usa o nome (ou o email se o nome estiver vazio)
      setNomeUsuario(data.nome || emailName)
      
      // Respeita o step salvo no banco
      if (typeof data.step === 'number' && data.step > 0) {
          setEtapaAtual(data.step)
      }
    } else {
      // Se não achou registro no banco, usa o email e começa na etapa 1
      setNomeUsuario(emailName)
      setEtapaAtual(1)
    }
    
    setLoading(false)
  }, [])

  useEffect(() => {
    autenticarECarregarCandidato()
  }, [autenticarECarregarCandidato])

  // --- HANDLERS DO FLUXO DE DOCUMENTOS ---
  const handleProcessamentoIniciado = (novoBatchId: string) => {
    console.log("Batch iniciado:", novoBatchId);
    setBatchId(novoBatchId); 
    setEtapaAtual(4); // Vai para Análise
  };

  const handleAnaliseConcluida = () => {
    console.log("Análise concluída.");
    setEtapaAtual(5); // Vai para Resultado
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