import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './register.scss'
import SilviaIAIndex from '/images/SilviaIAIndex.png'
import iconePuc from '/icons/iconePuc.png'
import { supabase } from '../../supabaseClient'
import { useToast } from '../../context/ToastContext' // <--- Importar

export function Register() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const navigate = useNavigate()
  const { showToast } = useToast() // <--- Hook

  const handleRegister = async () => {
    if (!email.trim() || !senha.trim()) {
      setErro('Preencha todos os campos.');
      return;
    }

    const { error } = await supabase.auth.signUp({
      email,
      password: senha,
    });

    if (error) {
      setErro(error.message);
      // Também mostra um toast de erro para garantir visibilidade
      showToast(error.message, 'error');
      return;
    }

    // UX Melhorada: Feedback visual positivo antes de navegar
    showToast('Conta criada com sucesso! Verifique seu e-mail.', 'success');
    
    // Pequeno delay para o usuário ler a mensagem
    setTimeout(() => {
        navigate('/'); 
    }, 2000);
  };

  return (
    <div className="login-page">
      <div className="left">
        <img src={iconePuc} alt="PUC Campinas" className="logo" />
        <div className="form-box">
          <h2>Registrar conta</h2>
          <form
            onSubmit={e => {
              e.preventDefault();
              handleRegister();
            }}
          >
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
            <input
              type="password"
              placeholder="Senha"
              value={senha}
              onChange={e => setSenha(e.target.value)}
            />
            {erro && <p className="error">{erro}</p>}
            <button className="button" type="submit">
              Registrar
            </button>
            <button
              className="button google"
              type="button"
              onClick={() => navigate('/')}
            >
              Voltar
            </button>
          </form>
        </div>
      </div>

      <div className="right">
        <div className="branding">
          <h1><strong>CAA</strong> VIRTUAL</h1>
          <div className="bot">
            <img src={SilviaIAIndex} alt="Chatbot" />
          </div>
        </div>
      </div>
    </div>
  )
}