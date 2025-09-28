"use client";
import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { SpinningLogo } from "@/components/SpinningLogo";
import { VideoDisplay } from "@/components/VideoDisplay";
import { useFirebaseAuth } from "@/hooks/useFirebaseAuth";
import { onAuthStateChanged, User } from "firebase/auth";

interface NotesData {
  id: number;
  firebase_uid: string;
  title: string;
  notes_link: string;
  status: string;
  videos_link: string;
}

export default function VideosPage() {
  const params = useParams();
  const router = useRouter();
  const postId = params.post as string;
  const auth = useFirebaseAuth();
  const [user, setUser] = useState<User | null>(null);
  const [notes, setNotes] = useState<NotesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // Listen for auth state changes
  useEffect(() => {
    if (auth) {
      const unsubscribe = onAuthStateChanged(auth, (user) => {
        setUser(user);
      });
      return () => unsubscribe();
    }
  }, [auth]);

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Function to fetch notes data
  const fetchNotesData = async () => {
    if (!user || !postId) return;

    try {
      const token = await user.getIdToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/notes/${postId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('API Response Status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('API Response Data:', JSON.stringify(data, null, 2));
        
        const notesData = data.notes;
        setNotes(notesData);
        setError("");

        // ONLY stop polling when status is exactly "completed"
        if (notesData.status === 'completed') {
          console.log('Status is completed, stopping polling...');
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
          setLoading(false);
        } else {
          console.log('Status is not completed yet:', notesData.status);
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.log('API Error Response:', response.status, errorData);
        
        if (response.status === 404) {
          setError("Notes not found");
          setLoading(false);
        } else if (response.status === 403) {
          setError("Access denied");
          setLoading(false);
        } else {
          setError("Failed to fetch notes data");
          setLoading(false);
        }
      }
    } catch (error) {
      console.error('Error fetching notes data:', error);
      setError("Network error occurred");
      setLoading(false);
    }
  };

  // Start polling when component mounts and user is available
  useEffect(() => {
    if (user && postId && !pollingInterval) {
      // Fetch immediately
      fetchNotesData();
      
      // Then poll every 5 seconds
      const interval = setInterval(() => {
        fetchNotesData();
      }, 5000);
      setPollingInterval(interval);
    }
  }, [user, postId, pollingInterval]);

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
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Videos" />
        <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
          <p className="text-center">You must be logged in to view videos.</p>
          <button
            onClick={() => router.push('/login')}
            className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Go to Login
          </button>
        </div>
      </main>
    );
  }

  // Show error state
  if (error) {
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Error" />
        <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
          <p className="text-center text-red-200">{error}</p>
          <button
            onClick={() => router.push('/create')}
            className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Back to Upload
          </button>
        </div>
      </main>
    );
  }

  // Show processing state with spinning logo
  if (loading) {
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Processing Videos" />
        <div className="flex flex-col items-center space-y-6 mt-10">
          <SpinningLogo size="lg" />
          <div className="text-center">
            <p className="text-xl font-semibold">Processing your videos...</p>
            <p className="text-sm text-gray-200 mt-2">
              Status: {notes?.status || "Starting..."}
            </p>
            <p className="text-xs text-gray-300 mt-1">
              Notes ID: {postId}
            </p>
          </div>
        </div>
      </main>
    );
  }

  // Show videos when completed
  if (notes && notes.status === 'completed' && notes.videos_link) {
    const videoUrls = notes.videos_link.split(',').map(url => url.trim());
    
    return (
      <main className="relative min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4 py-8">
        <VideoDisplay 
          videoUrls={videoUrls} 
          onBack={() => router.push('/create')} 
        />
      </main>
    );
  }

  // Fallback loading state
  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
      <Header headerText="Loading Videos" />
      <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
        <SpinningLogo size="md" />
        <p>Loading...</p>
      </div>
    </main>
  );
}
