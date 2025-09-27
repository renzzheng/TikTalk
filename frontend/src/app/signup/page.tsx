"use client";
import React, { useState } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { useFirebaseAuth } from "../../hooks/useFirebaseAuth";
import { FirebaseError } from "firebase/app";
import { useRouter } from "next/navigation"; // ✅ import router

export default function SignUp() {
  const auth = useFirebaseAuth();
  const router = useRouter(); // ✅ initialize router

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const validatePassword = (pwd: string) => {
    if (pwd.length > 8) return "Password must be at most 8 characters long";
    if ((pwd.match(/[0-9]/g) || []).length < 3)
      return "Password must contain at least 3 numbers";
    if (!/[A-Z]/.test(pwd)) return "Password must contain at least 1 uppercase letter";
    if (!/[!_@#$]/.test(pwd)) return "Password must contain at least 1 special character (!, _, @, #, $)";
    return "";
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!auth) {
      setError("Firebase Auth is not ready yet.");
      return;
    }

    const validationError = validatePassword(password);
    if (validationError) {
      setError(validationError);
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setError("");
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      const token = await user.getIdToken();

      console.log("User created:", user.uid);
      console.log("Token:", token);

      const apiUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/users/register`;
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: (document.getElementById("full_name") as HTMLInputElement).value,
          username: (document.getElementById("username") as HTMLInputElement).value,
          email,
        }),
      });

      const json = await res.json();
      console.log("API response:", json);

      if (res.ok) {
        router.push("/");
      } else {
        setError(json.error || "Failed to register user");
      }
    } catch (err) {
      if (err instanceof FirebaseError) {
        console.error(err);
        setError(err.message);
      } else {
        console.error(err);
        setError("Unexpected error occurred.");
      }
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Create Account
        </h1>
        <form onSubmit={handleSignUp} className="space-y-4">
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
              Full Name
            </label>
            <input
              type="text"
              id="full_name"
              className="text-black mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md 
                         shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              type="text"
              id="username"
              className="text-black mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md 
                         shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
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
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="text-black mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md 
                         shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="text-black mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md 
                         shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 
                       transition-colors font-medium"
          >
            Sign Up
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <a href="/login" className="text-blue-600 hover:underline">
            Log in
          </a>
        </p>
      </div>
    </div>
  );
}
