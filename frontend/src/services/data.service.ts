import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/',
});

export const getChecklist = async () => {
  try {
    const response = await api.get('/checklist');
    console.log('Checklist:', response.data);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar checklist:', error);
    throw error;
  }
};