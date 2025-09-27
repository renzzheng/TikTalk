"use client";

import { useEffect, useState } from "react";
import { getAuth, Auth } from "firebase/auth";
import { getFirebaseApp } from "../services/firebase";

export function useFirebaseAuth(): Auth | null {
  const [auth, setAuth] = useState<Auth | null>(null);

  useEffect(() => {
    try {
      const app = getFirebaseApp(); // initialize app **inside the hook**
      const authInstance = getAuth(app);

      setAuth(authInstance);
    } catch (err) {
      console.error("Firebase Auth init failed:", err);
    }
  }, []);

  return auth;
}