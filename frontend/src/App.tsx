import { SignIn } from './pages/candidates/Signin/index';
import { SignInF } from './pages/funcionario/Signin/indexF';
import { HomeF } from './pages/funcionario/Home/homeF';
import { Home } from './pages/candidates/Home/home';
import './styles/global.scss';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Register } from './pages/Register/register';
import LandingPage from './pages/landing-page/Index';
import { ToastProvider } from './context/ToastContext'; // <--- IMPORTANTE

export default function App() {
  return (
    <ToastProvider> {/* <--- ENVOLVE TUDO AQUI */}
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login/funcionario" element={<SignInF />} />
          <Route path="/homeF" element={<HomeF />} />
          <Route path="/login/candidato" element={<SignIn />} />
          <Route path="/home" element={<Home />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </Router>
    </ToastProvider>
  );
}