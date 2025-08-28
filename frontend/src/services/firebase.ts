import { initializeApp } from "firebase/app";
import { getAuth } from 'firebase/auth';
import { getStorage } from 'firebase/storage';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyDiGc79GAGRDIIto6yw2UP1gQOY0HSDT6A",
  authDomain: "project-tcc-7a061.firebaseapp.com",
  projectId: "project-tcc-7a061",
  storageBucket: "project-tcc-7a061.firebasestorage.app",
  messagingSenderId: "656896976970",
  appId: "1:656896976970:web:d631df65cbef8591429eb3"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const storage = getStorage(app);
export const db = getFirestore(app);