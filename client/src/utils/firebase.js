
import { initializeApp } from "firebase/app";
import {getAuth, GoogleAuthProvider} from "firebase/auth";

const firebaseConfig = {
  apiKey:import.meta.env.VITE_FIREBASE_APIKEY ,
  authDomain: "evalai-ce1f9.firebaseapp.com",
  projectId: "evalai-ce1f9",
  storageBucket: "evalai-ce1f9.firebasestorage.app",
  messagingSenderId: "927794448155",
  appId: "1:927794448155:web:00485df292a24ef6e7f5be"
};

const app = initializeApp(firebaseConfig);

const auth = getAuth(app)

const provider = new GoogleAuthProvider()

export {auth , provider}