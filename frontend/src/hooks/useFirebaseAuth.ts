"use client";

import { useEffect, useState } from "react";
import { getAuth, Auth, onAuthStateChanged, signOut } from "firebase/auth";
import { getFirebaseApp } from "../services/firebase";
import { useRouter } from "next/navigation";


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

export function isUserLoggedIn() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null); // null = loading

  useEffect(() => {
    const app = getFirebaseApp();
    const auth = getAuth(app);

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      console.log(user);
      setLoggedIn(user ? true : false);
    });

    return () => unsubscribe();
  }, []);

  console.log(loggedIn);
  return loggedIn;
}

export function signUserOut() {
  const app = getFirebaseApp();
  const auth = getAuth(app);

  signOut(auth)
    .then(() => {
      console.log("User signed out");
      if (typeof window !== "undefined") {
        localStorage.removeItem("authToken");
      }
    })
    .catch((error) => {
      console.error("Sign out error:", error);
    });
  }