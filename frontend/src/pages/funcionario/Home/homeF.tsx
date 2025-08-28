import { useEffect, useState } from 'react'
import { supabase } from '../../../supabaseClient'
import UserMenu from '../../../components/User-menu/User-menu'
import './homeF.scss'
import logo from '../../../assets/svg/logo.svg'
import gradientSvg from '../../../assets/svg/gradient.svg'
import { ChevronDown } from 'lucide-react'

interface FileEntry {
  fileName: string
  publicUrl: string
  status?: string
}

interface CandidateFiles {
  id: string
  name: string
  files: FileEntry[]
}

export function HomeF() {
  const [candidateFiles, setCandidateFiles] = useState<CandidateFiles[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const [modalOpen, setModalOpen] = useState(false)
  const [justificativa, setJustificativa] = useState('')
  const [selectedFile, setSelectedFile] = useState<{ candidatoId: string, fileUrl: string } | null>(null)

  const checkAndUpdateStep = async (candidatoId: string, files: FileEntry[]) => {
    const allValidated = files.every(
      f => f.status === 'aceito' || f.status === 'recusado'
    );
    if (allValidated) {
      // Obtenha o token do usuário autenticado pelo Supabase
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      await fetch('http://localhost:5000/candidato/step', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ candidato_id: candidatoId, step: 5 })
      });
      console.log('Etapa atualizada para 5');
    }
  };

  // Busca status dos documentos do backend
  const fetchStatuses = async (files: FileEntry[], candidato_id: string) => {
    try {
      const res = await fetch(`http://localhost:5000/documento/status?candidato_id=${candidato_id}`)
      if (!res.ok) return files
      const statusObj = await res.json() // { [file_path]: status }
      return files.map(f => ({
        ...f,
        status: statusObj[f.publicUrl] // status pode ser 'aceito', 'recusado' ou undefined
      }))
    } catch {
      return files
    }
  }

  useEffect(() => {
    const fetchData = async () => {
      const { data: candidates } = await supabase
        .from('candidate')
        .select('id, nome')

      const bucket = supabase.storage.from('documents')
      const { data: folders } = await bucket.list('', { limit: 100 })
      if (!folders) return

      const result: CandidateFiles[] = []
      for (const folder of folders) {
        if (!folder.name.startsWith('candidato_')) continue

        const candidateId   = folder.name.replace('candidato_', '')
        const candidateName = candidates?.find(c => c.id === candidateId)?.nome || candidateId

        // percorre subpastas de documentos
        const { data: docFolders } = await bucket.list(folder.name, { limit: 100 })
        if (!docFolders) continue

        let files: FileEntry[] = []
        for (const docFolder of docFolders) {
          const docPath = `${folder.name}/${docFolder.name}`
          const { data: items } = await bucket.list(docPath, { limit: 100 })
          if (!items) continue

          for (const item of items) {
            const filePath = `${docPath}/${item.name}`
            const { data } = bucket.getPublicUrl(filePath)
            const publicUrl = data.publicUrl

            files.push({
              fileName: item.name,
              publicUrl
            })
          }
        }

        // Busca status dos documentos e adiciona ao objeto files
        files = await fetchStatuses(files, candidateId)

        result.push({ id: candidateId, name: candidateName, files })
      }

      setCandidateFiles(result)
    }

    fetchData()
  }, [])

  const toggle = (id: string) =>
    setExpandedId(expandedId === id ? null : id)

  const updateFileStatus = (candidatoId: string, fileUrl: string, status: string) => {
    setCandidateFiles(prev =>
      prev.map(cf =>
        cf.id === candidatoId
          ? {
              ...cf,
              files: cf.files.map(f =>
                f.publicUrl === fileUrl ? { ...f, status } : f
              )
            }
          : cf
      )
    )
  }

  return (
    <div className="homeF-container">
      <header>
        <img src={logo} alt="Logo" className="logo" />
        <UserMenu
          userName="Funcionário"
          userEmail="funcionario@exemplo.com"
          userImage=""
          onLogout={() => supabase.auth.signOut()}
        />
      </header>

      <main className="docs-section">
        <h2>Avaliar documentos para aprovação da bolsa</h2>
        <p className="subtitle">Documentos enviados por candidatos</p>

        <div className="candidates-list">
          {candidateFiles.map(cf => {
            const isOpen = expandedId === cf.id
            return (
              <div
                key={cf.id}
                className={`candidate-card ${isOpen ? 'open' : ''}`}
              >
                <div
                  className="card-header"
                  onClick={() => toggle(cf.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <span className="candidate-name">{cf.name}</span>
                  <div className="card-controls">
                    <ChevronDown
                      className={`chevron-icon ${isOpen ? 'rotated' : ''}`}
                    />
                  </div>
                </div>

                {isOpen && (
                  <div className="card-body">
                    {cf.files.length === 0 ? (
                      <p style={{ color: '#ccc' }}>Nenhum documento enviado.</p>
                    ) : (
                      <ul>
                        {cf.files.map(f => {
                          const isFinal = f.status === 'aceito' || f.status === 'recusado'
                          return (
                            <li
                              key={f.publicUrl}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '1rem',
                                marginBottom: '0.5rem',
                                background: isFinal
                                  ? f.status === 'aceito'
                                    ? '#e6f9ed'
                                    : '#fbeaea'
                                  : 'transparent',
                                borderRadius: '4px',
                                opacity: isFinal ? 0.7 : 1,
                                textDecoration: isFinal ? 'line-through' : 'none'
                              }}
                            >
                              <a
                                href={f.publicUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="file-link"
                                style={{
                                  flex: 1,
                                  pointerEvents: isFinal ? 'none' : 'auto',
                                  color: isFinal ? '#888' : undefined
                                }}
                              >
                                <span
                                  className="file-icon"
                                  style={{
                                    color: '#007bff',
                                    fontSize: '1.2rem',
                                    marginRight: '0.5rem'
                                  }}
                                >
                                  📎
                                </span>
                                {f.fileName}
                              </a>
                              <button
                                style={{
                                  background: '#28a745',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: 4,
                                  padding: '0.3rem 0.8rem',
                                  cursor: isFinal ? 'not-allowed' : 'pointer',
                                  opacity: isFinal ? 0.5 : 1
                                }}
                                disabled={isFinal}
                                onClick={async () => {
                                  await fetch('http://localhost:5000/documento/status', {
                                    method: 'PATCH',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      candidato_id: cf.id,
                                      file_path: f.publicUrl,
                                      status: 'aceito'
                                    })
                                  });
                                  updateFileStatus(cf.id, f.publicUrl, 'aceito');
                                  // Atualize a lista de arquivos já com o novo status
                                  const updatedFiles = cf.files.map(file =>
                                    file.publicUrl === f.publicUrl ? { ...file, status: 'aceito' } : file
                                  );
                                  checkAndUpdateStep(cf.id, updatedFiles);
                                }}
                              >
                                Aceitar
                              </button>
                              <button
                                style={{
                                  background: '#dc3545',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: 4,
                                  padding: '0.3rem 0.8rem',
                                  cursor: isFinal ? 'not-allowed' : 'pointer',
                                  opacity: isFinal ? 0.5 : 1
                                }}
                                disabled={isFinal}
                                onClick={() => {
                                  setSelectedFile({ candidatoId: cf.id, fileUrl: f.publicUrl })
                                  setModalOpen(true)
                                  setJustificativa('')
                                }}
                              >
                                Recusar
                              </button>
                              {f.status && (
                                <span
                                  style={{
                                    marginLeft: '0.5rem',
                                    fontWeight: 500,
                                    color:
                                      f.status === 'aceito'
                                        ? '#28a745'
                                        : f.status === 'recusado'
                                        ? '#dc3545'
                                        : '#888'
                                  }}
                                >
                                  {f.status === 'aceito'
                                    ? 'Aceito'
                                    : f.status === 'recusado'
                                    ? 'Recusado'
                                    : ''}
                                </span>
                              )}
                            </li>
                          )
                        })}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
          {modalOpen && (
            <div className="modal-overlay">
              <div className="modal-box">
                <h3>Justificativa da recusa</h3>
                <textarea
                  value={justificativa}
                  onChange={e => setJustificativa(e.target.value)}
                  placeholder="Digite o motivo da recusa..."
                  style={{ width: '100%', minHeight: 80, marginBottom: 16 }}
                />
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <button onClick={() => setModalOpen(false)}>Cancelar</button>
                    <button
                      style={{ background: '#dc3545', color: '#fff', border: 'none', borderRadius: 4, padding: '0.3rem 0.8rem' }}
                      disabled={!justificativa.trim()}
                      onClick={async () => {
                        if (!selectedFile) return
                        await fetch('http://localhost:5000/documento/status', {
                          method: 'PATCH',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            candidato_id: selectedFile.candidatoId,
                            file_path: selectedFile.fileUrl,
                            status: 'recusado',
                            justificativa
                          })
                        })
                        updateFileStatus(selectedFile.candidatoId, selectedFile.fileUrl, 'recusado')
                        const cf = candidateFiles.find(c => c.id === selectedFile.candidatoId)
                        if (cf) {
                          const updatedFiles = cf.files.map(file =>
                            file.publicUrl === selectedFile.fileUrl ? { ...file, status: 'recusado' } : file
                          )
                          checkAndUpdateStep(selectedFile.candidatoId, updatedFiles)
                        }
                        setModalOpen(false)
                        setJustificativa('')
                        setSelectedFile(null)
                      }}
                  >
                    Confirmar
                  </button>
                </div>
              </div>
            </div>
        )}
      </main>
    </div>
  )
}