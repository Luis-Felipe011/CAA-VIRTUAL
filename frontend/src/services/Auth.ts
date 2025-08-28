import { supabase } from '../supabaseClient'

interface LoginData {
  email: string
  senha: string
}

export async function sendMessage(msg_bot: string, mensagem: string) {
  const {
    data: { user },
    error: userError
  } = await supabase.auth.getUser();

  if (userError || !user) {
    console.error('Erro ao obter usuário:', userError);
    return;
  }


  const { data, error } = await supabase
    .from('sessao')
    .insert([
      {
        user_id: user.id,
        msg_bot: msg_bot, // 'user' ou 'bot'
        mensagem: mensagem
      }
    ]);

  if (error) {
    console.error('Erro ao inserir mensagem:', error);
  } else {
    console.log('Mensagem inserida:', data);
  }
}

export const registrarUsuario = async (dados: LoginData) => {
  const { data, error } = await supabase.auth.signUp({
    email: dados.email,
    password: dados.senha,
  });

  if (error) {
    return { success: false, error: error.message }
  }

  return { success: true, data }
}

export async function ensureCandidateRecord(userId: string, email: string) {
  console.log(email, userId)
  const { data } = await supabase
    .from('candidate')
    .select('id')
    .eq('id', userId)
    .single();

  console.log('Data:', data);
  if (!data || data == null) {
  
    await supabase
      .from('candidate')
      .insert([{ id: userId, nome: '', cpf: '', email: email}]);
  }
}

export const loginUsuario = async (dados: LoginData) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: dados.email,
    password: dados.senha,
  });

  if (error) {
    return { success: false, error: error.message }
  }

  return { success: true, data }
}

export const createAccount = registrarUsuario
