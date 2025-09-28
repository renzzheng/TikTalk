"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../components/Button";
import { Header } from "../components/Header";
import { NotesGrid } from "../components/NotesGrid";
import Image from "next/image";
import { useFirebaseAuth } from "../hooks/useFirebaseAuth";
import { onAuthStateChanged, User } from "firebase/auth";

interface Note {
  id: number;
  firebase_uid: string;
  title: string;
  notes_link: string;
  status: string;
  videos_link: string | null;
  created_at: string;
}

export default function Home() {
  const router = useRouter();
  const auth = useFirebaseAuth();
  const [user, setUser] = useState<User | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Listen for auth state changes
  useEffect(() => {
    if (auth) {
      const unsubscribe = onAuthStateChanged(auth, async (user) => {
        setUser(user);
        if (user) {
          // Fetch user's notes
          try {
            setLoading(true);
            const token = await user.getIdToken();
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/notes/my-notes`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            });

            if (response.ok) {
              const data = await response.json();
              setNotes(data.notes || []);
              setError(null);
            } else {
              setError('Failed to fetch notes');
            }
          } catch (error) {
            console.error('Error fetching notes:', error);
            setError('Network error occurred');
          } finally {
            setLoading(false);
          }
        } else {
          setLoading(false);
        }
      });
      return () => unsubscribe();
    }
  }, [auth]);

  const handleGetStarted = () => {
    router.push("/create");
  };

  const notLogged = (
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
  
  // Show loading state while auth is initializing
  if (!auth) {
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Loading..." />
        <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
          <p>Loading...</p>
        </div>
      </main>
    );
  }

  // Show login prompt if user is not authenticated
  if (!user) {
    return notLogged;
  }

  // Show logged in user with notes
  return (
    <main className="relative min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <Header
            headerText="Your TikTalk Videos"
            subtext="Click on any video to view and manage your generated content."
          />
          <Button onClick={handleGetStarted}>Upload More Files</Button>
        </div>
        
        <NotesGrid 
          notes={notes} 
          loading={loading} 
          error={error} 
        />
      </div>
    </main>
  );
    
}