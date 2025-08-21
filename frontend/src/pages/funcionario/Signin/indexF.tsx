// src/pages/candidates/Signin/index.tsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './styles.scss'
import SilviaIAIndex from '/images/SilviaIAIndex.png'
import iconePuc      from '/icons/iconePuc.png'
import { loginUsuario } from '../../../services/Auth'

export function SignInF() {
  const [email, setEmail]   = useState('')
  const [senha, setSenha]   = useState('')
  const [erro, setErro]     = useState('')
  const navigate            = useNavigate()

  const handleLogin = async () => {
    // 1) checa campos vazios
    if (!email.trim() || !senha.trim()) {
      setErro('Preencha email e senha.')
      return
    }

    const emailLower = email.trim().toLowerCase()

    // 2) só permite esse e-mail específico
    if (emailLower !== 'nas.puc@outlook.com') {
      setErro('Email não autorizado.')
      return
    }

    // 3) chama sua API/Supabase para validar a senha
    const { success, error } = await loginUsuario({ email, senha })
    if (!success) {
      setErro(error ?? 'Erro desconhecido')
      return
    }
    navigate('/homeF')
  }

  return (
    <div className="login-page">
      <div className="left">
        <img src={iconePuc} className="logo" alt="PUC Campinas" />
        <div className="form-box">
          <h2>Login</h2>

          <form
            onSubmit={e => {
              e.preventDefault();
              handleLogin();
            }}
          >
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => { setEmail(e.target.value); setErro('') }}
            />

            <input
              type="password"
              placeholder="Senha"
              value={senha}
              onChange={e => { setSenha(e.target.value); setErro('') }}
            />

            {erro && <p className="error">{erro}</p>}

            <button className="button" type="submit">
              Entrar
            </button>
          </form>

          

          
        </div>
      </div>

      <div className="right">
        <div className="branding">
          <h1><strong>NAS</strong> VIRTUAL</h1>
          <h2>ATENDENTE</h2>
          <div className="bot">
            <img src={SilviaIAIndex} alt="Chatbot" />
          </div>
        </div>
      </div>
    </div>
  )
}
