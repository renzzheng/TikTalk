"use client";
import React from "react";
import { useRouter } from "next/navigation";
import { Button } from "../components/Button";
import { Header } from "../components/Header";
import Image from "next/image";

export default function Home() {
  const router = useRouter(); // initialize the router

  const handleGetStarted = () => {
    router.push("/create"); // navigate to the upload page
  };

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
      <div className="flex flex-col items-center justify-center text-center space-y-6 flex-grow">
        <Header 
          headerText="Welcome to TikTalk" 
          subtext="Discover a new way to create, share, and comment. Our platform makes it simple and intuitive to get started."
        />
        <Button onClick={handleGetStarted}>Get Started</Button>

        <div className="flex gap-6 mt-10 items-center">
          <div className="group relative w-64 h-64 rounded-2xl overflow-hidden shadow-lg cursor-pointer transform transition duration-300 hover:scale-105 hover:shadow-2xl">
            <Image
              src="/pdfimg.png"
              alt="Sample 1"
              fill
              className="object-cover transition-opacity duration-300 group-hover:opacity-80"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-center p-2 opacity-0 group-hover:opacity-100 transition duration-300">
              PDF
            </div>
          </div>

          <div className="group relative w-64 h-64 rounded-2xl overflow-hidden shadow-lg cursor-pointer transform transition duration-300 hover:scale-105 hover:shadow-2xl">
            <Image
              src="/mp4img.png"
              alt="Sample 2"
              fill
              className="object-cover transition-opacity duration-300 group-hover:opacity-80"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-center p-2 opacity-0 group-hover:opacity-100 transition duration-300">
              MP4
            </div>
          </div>

          <Image
            src="/blackarrow.png"
            alt="Arrow"
            width={200}
            height={200}
            className="animate-bounce"
          />

          <div className="group relative w-64 h-64 rounded-2xl overflow-hidden shadow-lg cursor-pointer transform transition duration-300 hover:scale-105 hover:shadow-2xl">
            <Image
              src="/ttlogo.svg"
              alt="Sample 3"
              fill
              className="object-cover transition-opacity duration-300 group-hover:opacity-80"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-center p-2 opacity-0 group-hover:opacity-100 transition duration-300">
              TIKTALK
            </div>
          </div>
        </div>
      </div>

      <div className="absolute left-6 bottom-6 w-72">
        <h1 className="text-6xl font-bold text-white mb-2">About Us</h1>
        <p className="text-sm min-w-screen text-white">
          We are college student full stack software developers building a
          platform to allow users to share their content, lectures, or study
          materials in multiple formats where our web app will generate short
          form videos from videos, pdfs, mp4s, etc!
        </p>
      </div>
    </main>
  );
}