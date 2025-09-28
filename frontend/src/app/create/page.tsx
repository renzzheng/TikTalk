"use client";
import React, { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Button } from "@/components/Button";
import { SpinningLogo } from "@/components/SpinningLogo";
import { useFirebaseAuth } from "@/hooks/useFirebaseAuth";
import { onAuthStateChanged, User } from "firebase/auth";

export default function Upload() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [title, setTitle] = useState<string>("");
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const auth = useFirebaseAuth();

  const [currentNotesId, setCurrentNotesId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>("");
  const [pollingInterval, setPollingInterval] =
    useState<NodeJS.Timeout | null>(null);

  const MAX_FILES = 5;

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

  // Poll notes status
  const pollNotesStatus = async (notesId: number) => {
    if (!user) return;

    try {
      const token = await user.getIdToken();
        const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/notes/${notesId}`;
        console.log("[Polling] GET", url);

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      console.log("[Polling] Status:", response.status);

      let data: any = null;
      try {
        data = await response.json();
        console.log("[Polling] Response JSON:", JSON.stringify(data, null, 2));
      } catch (err) {
        console.error("[Polling] Failed to parse JSON:", err);
      }

      if (response.ok && data) {
        const notes = data.notes;
        setStatus(notes.status);

        if (notes.status === "completed") {
          console.log("✅ Notes completed, redirecting...");
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
          setProcessing(false);
          router.push(`/videos/${notesId}`);
        } else {
          console.log("⏳ Not completed yet:", notes.status);
        }
       } else {
         console.error("[Polling] Error Response:", response.status, data);
         setMessage(`API Error: ${response.status} - ${data?.error || 'Unknown error'}`);
       }
    } catch (error) {
      console.error("[Polling] Exception:", error);
      setMessage(`Network Error: ${error}`);
    }
  };

  // Start polling when notes ID is set
  useEffect(() => {
    if (currentNotesId && !pollingInterval) {
      console.log("▶️ Starting polling for notes", currentNotesId);
      console.log("▶️ API Base URL:", process.env.NEXT_PUBLIC_API_BASE_URL);
      const interval = setInterval(() => {
        pollNotesStatus(currentNotesId);
      }, 5000);
      setPollingInterval(interval);
    }
  }, [currentNotesId, pollingInterval, user]);

  // Reset state
  const resetState = () => {
    console.log("🛑 Resetting state");
    setCurrentNotesId(null);
    setStatus("");
    setMessage("");
    setTitle("");
    setSelectedFiles([]);
    setProcessing(false);
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  const handleSelectClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);

    const supportedTypes = [
      "application/pdf",
      "video/mp4",
      "video/quicktime",
      "video/x-msvideo",
      "audio/mpeg",
      "audio/wav",
      "audio/mp4",
      "audio/x-m4a",
    ];

    const validFiles = files.filter((file) => {
      if (!supportedTypes.includes(file.type)) {
        alert(
          `${file.name} is not supported. Supported: PDF, MP4, MP3, WAV, M4A`
        );
        return false;
      }
      return true;
    });

    if (validFiles.length + selectedFiles.length > MAX_FILES) {
      alert(`You can only upload up to ${MAX_FILES} files.`);
      return;
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadAndProcess = async () => {
    if (!title.trim()) {
      setMessage("Please enter a title for your video set ❌");
      return;
    }

    setProcessing(true);
    setMessage("");

    try {
      const uploadedUrls: string[] = [];

      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append("file", file);

        console.log("[Upload] POST /api/upload", file.name);
        const res = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });

        console.log("[Upload] Status:", res.status);

        try {
          const data = await res.json();
          console.log("[Upload] Response:", data);
          if (res.ok && data.url) {
            uploadedUrls.push(data.url);
          }
        } catch (err) {
          console.error("[Upload] Failed to parse JSON:", err);
        }
      }

      if (!user) {
        setMessage("You must be logged in to continue ❌");
        setProcessing(false);
        return;
      }

      const token = await user.getIdToken();
      const apiUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/files/process-files`;

      if (uploadedUrls.length > 0) {
        console.log("[Process] POST", apiUrl);
        const res2 = await fetch(apiUrl, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ title: title.trim(), file_urls: uploadedUrls }),
        });

        console.log("[Process] Status:", res2.status);

        let json: any = null;
        try {
          json = await res2.json();
          console.log("[Process] Response JSON:", json);
        } catch (err) {
          console.error("[Process] Failed to parse JSON:", err);
        }

         if (res2.ok && json && json.notes && json.notes.id) {
           setMessage("Processing started successfully ✅");
           setCurrentNotesId(json.notes.id);
           setStatus("not_started");
         } else {
           setMessage(json?.error || "Failed to start processing ❌");
           setProcessing(false);
         }
      }
    } catch (err) {
      console.error("[Upload/Process] Exception:", err);
      setMessage("Unexpected error occurred ❌");
      setProcessing(false);
    }
  };

  // --- Render ---
  if (!auth) {
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Upload Files" />
        <p>Loading...</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Upload Files" />
        <p>You must be logged in to upload files.</p>
        <Button onClick={() => (window.location.href = "/login")}>
          Go to Login
        </Button>
      </main>
    );
  }

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
      <Header headerText="Upload Files" />

      <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
        {/* Title Input */}
        <div className="w-full">
          <label htmlFor="title" className="block text-sm font-medium text-white mb-2">
            Video Set Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a title for your video set..."
            className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={processing}
            maxLength={100}
          />
          <p className="text-xs text-gray-300 mt-1">
            {title.length}/100 characters
          </p>
        </div>

        <Button onClick={handleSelectClick} disabled={processing}>
          Select Files
        </Button>
        <p className="text-sm text-gray-200">
          Accepted: PDF, MP4, MP3, WAV, M4A • Max {MAX_FILES} files • No size
          limit
        </p>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.mp4,.mp3,.wav,.m4a,.mov,.mkv"
          multiple
          className="hidden"
          disabled={processing}
        />

        {processing && (
          <div className="flex flex-col items-center space-y-4 mt-6">
            <SpinningLogo size="lg" />
            <div className="text-center">
              <p className="text-lg font-semibold">Processing your files...</p>
              <p className="text-sm text-gray-200">
                Status: {status || "Starting..."}
              </p>
              {currentNotesId && (
                <p className="text-xs text-gray-300 mt-1">
                  Notes ID: {currentNotesId}
                </p>
              )}
            </div>
            <button
              onClick={resetState}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
            >
              Cancel Processing
            </button>
          </div>
        )}

        {selectedFiles.length > 0 && !processing && (
          <div className="mt-6 w-full max-w-md bg-white text-gray-800 rounded-xl p-4 shadow-lg">
            <h2 className="font-semibold mb-2">Files ready to upload:</h2>
            <ul className="space-y-1">
              {selectedFiles.map((file, index) => (
                <li
                  key={index}
                  className="flex justify-between items-center border border-gray-300 rounded-md p-2"
                >
                  <span>
                    {file.name}{" "}
                    {file.size > 1024 * 1024
                      ? `${Math.round(file.size / (1024 * 1024))} MB`
                      : `${Math.round(file.size / 1024)} KB`}
                  </span>
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="ml-3 text-red-500 hover:text-red-700 font-bold"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
            <Button
              onClick={handleUploadAndProcess}
              className="mt-4"
              disabled={processing}
            >
              Upload & Process
            </Button>
            {message && <p className="mt-2 text-sm">{message}</p>}
          </div>
        )}
      </div>
    </main>
  );
}
