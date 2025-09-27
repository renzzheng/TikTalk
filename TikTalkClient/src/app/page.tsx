"use client";
import React from "react";
import { useRouter } from "next/navigation";
import { Button } from "../components/Button";
import { Header } from "../components/Header";

export default function Home() {
 const handleGetStarted = () => {
    // Replace this with navigation logic (React Router, Next.js router, etc.)
    console.log("Get Started clicked!");
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-center px-4">
      <Header headerText="Welcome hgjhgjhto Our App" />
      <Button onClick={handleGetStarted}>Get Started</Button>
    </main>
  ); 
}
