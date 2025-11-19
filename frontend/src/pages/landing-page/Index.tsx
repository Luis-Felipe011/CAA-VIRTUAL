import { useNavigate } from "react-router-dom"
import "./styles.scss"
import logo from '../../assets/svg/logo.svg';
import ilust from '../../assets/svg/ilust.svg';
import Button from "../../components/Button/Button"
import gradient from "../../assets/svg/gradient.svg";

const LandingPage = () => {
  const navigate = useNavigate()

  return (
    <div className="landing">
      <img className="img-gradient" src={gradient} alt="Background Gradient" />
      
      <header className="landing__header">
        <div className="logo">
          <img src={logo} alt="NAS Virtual Logo" />
        </div>
        <div className="nav">
           {/* Botão de acesso direto ao login do candidato */}
          <Button 
            onClick={() => navigate('/login/candidato')} 
            text='Acessar Portal' 
            color="primary"
            className="header-btn"
          />
        </div>
      </header>

      <main className="landing__main">
        <div className="text-block">
          <h1>Envio e Análise de Documentos Simplificada</h1>
          <p>
            Bem-vindo ao <strong>NAS VIRTUAL</strong>. A plataforma oficial para submissão 
            e acompanhamento dos documentos do Prouni.
            <br/>
            Conectamos você à instituição de forma simples, rápida e 100% digital, 
            sem filas e sem burocracia.
          </p>
          
          <div className="cta-group">
            <Button 
                onClick={() => navigate('/login/candidato')} 
                text="Começar Agora" 
                size="large" 
                className="main-cta"
            />
            <span className="sub-text">
              Ainda não tem cadastro? 
              <a onClick={() => navigate('/register')}> Criar conta</a>
            </span>
          </div>
        </div>
        
        <div className="image-block">
          <img src={ilust} alt="Ilustração de produtividade" className="floating-img" />
        </div>
      </main>
    </div>
  )
}

export default LandingPage