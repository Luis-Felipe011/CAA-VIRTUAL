import React, { useState } from 'react';
import { supabase } from "../../../supabaseClient"
import './Upload-table.scss';
import Button from '../../Button/Button';
import Badge from '../../badge/Badge';

interface Document {
  id: number;
  numero: string;
  nome: string;
  categoria: string;
}

interface UploadTableProps {
  documents: Document[];
  candidatoId: string;
  onStepChange?: (novoStep: number) => void; 
}

const UploadTable: React.FC<UploadTableProps> = ({ documents, candidatoId, onStepChange }) => {
  const [files, setFiles] = useState<{ [key: number]: File | null }>({});
  const [uploaded, setUploaded] = useState<{ [key: number]: boolean }>({});

  const handleFileChange = (id: number, file: File) => {
    setFiles((prevFiles) => ({
      ...prevFiles,
      [id]: file,
    }));
    setUploaded((prev) => ({
      ...prev,
      [id]: true,
    }));
  };

  const handleUpload = async () => {
    const { data: { user }, error } = await supabase.auth.getUser();
    console.log("Usuário autenticado:", user);

    for (const key of Object.keys(files)) {
      const id = parseInt(key);
      const file = files[id];
      if (file) {
        const doc = documents.find(d => d.id === id);
        const filePath = `candidato_${candidatoId}/documento_${id}/${file.name}`;
        const { data, error } = await supabase.storage
          .from('documents')
          .upload(filePath, file, { upsert: true });

        if (error) {
          console.error('Erro ao fazer upload:', error);
        } else {
          console.log('Upload realizado:', data);
          console.log('Documento:', doc);
          setUploaded(prev => ({ ...prev, [id]: true }));
        }
      }
    }

    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      const resposta = await fetch("http://localhost:5000/candidato/step", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ step: 4 }),
      });
      const json = await resposta.json();
      if (json.success) {
        alert("Documentos enviados e etapa atualizada!");
        if (onStepChange) {
          onStepChange(4);
        }
      } else {
        alert("Documentos enviados, mas houve erro ao atualizar etapa: " + json.error);
      }
    } catch (err) {
      alert("Erro ao atualizar etapa.");
    }
  };

  return (
    <div className="upload-table">
      <div className="document-list">
        {documents.map((doc) => (
          <div className="document-card" key={doc.id}>
            <div className="document-info">
              <div className="document-title">
                <span className="doc-num">{doc.numero}</span>
                <span className="doc-name">{doc.nome}</span>
              </div>
              <div className="document-category">{doc.categoria}</div>
            </div>
            <div className="document-actions">
              <div className="badge-wrapper">
                {uploaded[doc.id] ? (
                  <Badge color='info' text='Anexado' />
                ) : (
                  <Badge color='warning' text='Pendente' />
                )}
              </div>
              <label className="custom-file-label">
                <span className="file-icon">📎</span>
                <span>
                  {files[doc.id]?.name ? files[doc.id]?.name : "Selecionar arquivo"}
                </span>
                <input
                  type="file"
                  id={`file-input-${doc.id}`}
                  className="file-input"
                  onChange={(e) => {
                    if (e.target.files) {
                      handleFileChange(doc.id, e.target.files[0]);
                    }
                  }}
                />
              </label>
            </div>
          </div>
        ))}
      </div>
      <Button onClick={handleUpload} text='Enviar' color='primary' />
    </div>
  );
};

export default UploadTable;