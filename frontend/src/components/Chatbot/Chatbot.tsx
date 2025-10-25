import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import imgSilviaIA from '/images/silviaIA.png';
import './Chatbot.scss';
import { supabase } from '../../supabaseClient';

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<{ user: string; bot: string }[]>([]);
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage = input;
    setMessages([...messages, { user: userMessage, bot: 'Processando...' }]);
    setInput('');
    setIsLoading(true);

    // Obtenha o user_id do usuário autenticado
    const { data: { user } } = await supabase.auth.getUser();
    const user_id = user?.id;

    try {
  const response = await fetch('http://127.0.0.1:5004/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mensagem: userMessage, user_id }),
      });
      const result = await response.json();
      const botMessage = result.resposta;
      setMessages((prevMessages) => {
        const newMessages = [...prevMessages];
        newMessages[newMessages.length - 1].bot = botMessage;
        return newMessages;
      });
    } catch (error: any) {
      console.error('Erro ao enviar mensagem:', error);
      
      let errorDetails = '';
      if (error?.response?.data) {
        errorDetails = JSON.stringify(error.response.data);
      } else if (error?.message) {
        errorDetails = error.message;
      } else {
        errorDetails = String(error);
      }
      
      setMessages((prevMessages) => {
        const newMessages = [...prevMessages];
        newMessages[newMessages.length - 1].bot = `Erro: ${errorDetails}`;
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  return (
    <div className={`chatbot-container${isOpen ? ' open' : ''}`}>
      <div className={`chatbot${isOpen ? ' open' : ''}`}>
        {!isOpen && (
          <button
            className="chatbot-fab"
            aria-label="Abrir chat"
            onClick={() => setIsOpen(true)}
          >
            <img src={imgSilviaIA} alt="Abrir Chatbot" />
            <span className="chatbot-fab-tooltip">Fale com a Silvia</span>
          </button>
        )}

        {isOpen && (
          <div className="chatbot-content">
            <div className="chatbot-header">
              <img src={imgSilviaIA} alt="Silvia, assistente virtual" />
              <span>Silvia, assistente virtual</span>
              <button
                className="chatbot-close"
                aria-label="Fechar chat"
                onClick={() => setIsOpen(false)}
                type="button"
              >
                ×
              </button>
            </div>
            <div className="chatbot-messages">
              {messages.map((msg, index) => (
                <div key={index}>
                  <div className="chatbot-message-user">Você: {msg.user}</div>
                  <div className="chatbot-message-bot">Silvia: {msg.bot}</div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="chatbot-input">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Digite sua mensagem..."
                aria-label="Digite sua mensagem"
              />
              <button onClick={handleSendMessage} aria-label="Enviar mensagem">Enviar</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chatbot;