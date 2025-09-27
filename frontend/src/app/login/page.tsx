"use client";
import React from "react";
import { getFirebaseApp } from "@/services/firebase";
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";
import { FirebaseError } from "firebase/app";
import { useRouter } from "next/navigation";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const app = getFirebaseApp();
      const auth = getAuth(app);

      const userCred = await signInWithEmailAndPassword(auth, email, password);
      console.log(userCred.user.uid, "logged in successfully");

      router.push("/");
      return { success: true };
    } catch (err) {
      if (err instanceof FirebaseError) {
        switch (err.code) {
          case "auth/invalid-email":
            setError("Invalid email address");
            break;
          case "auth/user-disabled":
            setError("User account is disabled");
            break;
          case "auth/user-not-found":
            setError("No user found with this email");
            break;
          case "auth/wrong-password":
          case "auth/invalid-credential": // newer Firebase sometimes throws this instead
            setError("Incorrect password");
            break;
          default:
            setError(err.message);
        }
      } else {
        setError("Login failed");
      }
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Login
        </h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </label>
            <input
              type="email"
              id="email"
              className="text-black mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md 
                         shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              className={`mt-1 block w-full px-3 py-2 rounded-md shadow-sm focus:outline-none 
                         focus:ring-2 ${
                           error === "Incorrect password"
                             ? "border-red-500 focus:ring-red-500"
                             : "border-gray-300 focus:ring-blue-500"
                         }`}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error === "Incorrect password" && (
              <p className="mt-1 text-sm text-red-600">{error}</p>
            )}
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 
                       transition-colors font-medium"
          >
            Sign In
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Don’t have an account?{" "}
          <a href="/signup" className="text-blue-600 hover:underline">
            Sign up
          </a>
        </p>
        {error && error !== "Incorrect password" && (
          <p className="mt-3 text-center text-sm text-red-600">{error}</p>
        )}
      </div>
    </div>
  );
}
