import React from "react"
import { useNavigate } from "react-router-dom"
import "./styles.scss"
import logo from '../../assets/svg/logo.svg';
import ilust from '../../assets/svg/ilust.svg';
import Button from "../../components/Button/Button"
import  gradient  from "../../assets/svg/gradient.svg";


const LandingPage = () => {
  const navigate = useNavigate()

  return (
      <div className="landing">
        <img className="img-gradient" src={gradient} alt="" />
      <header className="landing__header">
        <div className="logo">
          <img src={logo} alt="" />
        </div>
        <div className="nav">
          <Button onClick={() => navigate('/login/candidato')} text='Sou Candidato'/>
          <Button onClick={() => navigate('/login/funcionario')} text="Sou Atendente" color="outline"/>
        </div>
      </header>

      <main className="landing__main">
        <div className="text-block">
          <p>
            Um sistema desenvolvido para facilitar o envio e análise dos documentos exigidos pelo
            programa Prouni, conectando candidatos e instituições de forma simples, rápida e segura.
          </p>
        </div>
        <div className="image-block">
          <img src={ilust} alt="Ilustração de documentos" />
        </div>
      </main>
    </div>
  )
}

export default LandingPage
