// src/pages/candidates/Signin/index.tsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './styles.scss'
import SilviaIAIndex   from '/images/SilviaIAIndex.png'
import iconePuc        from '/icons/iconePuc.png'
import { loginUsuario } from '../../../services/Auth'
import { ensureCandidateRecord } from '../../../services/Auth'

export function SignIn() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro]   = useState('')
  const navigate          = useNavigate()


const handleLogin = async () => {
  if (!email.trim() || !senha.trim()) {
    setErro('Preencha email e senha.');
    return;
  }

  const resultado = await loginUsuario({ email, senha });
  if (resultado.success) {
    const user = resultado.data?.user;
    if (user && user.id && user.email) {
      await ensureCandidateRecord(user.id, user.email);
    }
    navigate('/home');
  } else {
    setErro(resultado.error ?? 'Erro desconhecido');
  }
};

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

          <p>
            Não tem conta?{' '}
            <a href="/register" onClick={e => { e.preventDefault(); navigate('/register') }}>
              Criar uma conta
            </a>
          </p>
        </div>
      </div>

      <div className="right">
        <div className="branding">
          <h1><strong>NAS</strong> VIRTUAL</h1>
          <div className="bot">
            <img src={SilviaIAIndex} alt="Chatbot" />
          </div>
        </div>
      </div>
    </div>
  )
}
