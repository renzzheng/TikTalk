"use client";
import React, { useRef, useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { Button } from "@/components/Button";
import { useFirebaseAuth } from "@/hooks/useFirebaseAuth";
import { onAuthStateChanged, User } from "firebase/auth";

export default function Upload() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const auth = useFirebaseAuth();

  const MAX_FILES = 5;
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  // Listen for auth state changes
  useEffect(() => {
    if (auth) {
      const unsubscribe = onAuthStateChanged(auth, (user) => {
        setUser(user);
      });
      return () => unsubscribe();
    }
  }, [auth]);

  const handleSelectClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files);

    const validFiles = files.filter((file) => {
      if (file.type !== "application/pdf") {
        alert(`${file.name} is not a PDF file.`);
        return false;
      }
      if (file.size > MAX_FILE_SIZE) {
        alert(`${file.name} exceeds the 10MB size limit.`);
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
    setProcessing(true);
    setMessage("");
  
    try {
      const uploadedUrls: string[] = [];
  
      // Step 1: Upload files to Next.js API route → returns signed GCS URLs
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append("file", file);
  
        const res = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });
  
        if (res.ok) {
          const data = await res.json();
          uploadedUrls.push(data.url);
          console.log(`${file.name} uploaded → ${data.url}`);
        } else {
          console.error(`Failed to upload ${file.name}`);
        }
      }
  
      // Step 2: Get Firebase ID token
      if (!user) {
        setMessage("You must be logged in to continue ❌");
        setProcessing(false);
        return;
      }

      const token = await user.getIdToken();
  
      // Step 3: Call Flask /process-pdf API with Bearer token
      console.log(token)
      if (uploadedUrls.length > 0) {
        const apiUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/files/process-pdf`;
        const res2 = await fetch(apiUrl, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ pdf_urls: uploadedUrls }),
        });
  
        const json = await res2.json();
        console.log("Process API response:", json);
  
        if (res2.ok) {
          setMessage("Processing started successfully ✅");
        } else {
          setMessage(json.error || "Failed to start processing ❌");
        }
      }
    } catch (err) {
      console.error("Upload/Process error:", err);
      setMessage("Unexpected error occurred ❌");
    } finally {
      setProcessing(false);
    }
  };
  

  // Show loading state while auth is initializing
  if (!auth) {
    return (
      <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
        <Header headerText="Upload PDFs" />
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
        <Header headerText="Upload PDFs" />
        <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
          <p className="text-center">You must be logged in to upload files.</p>
          <Button onClick={() => window.location.href = '/login'}>Go to Login</Button>
        </div>
      </main>
    );
  }

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
      <Header headerText="Upload PDFs" />

      <div className="flex flex-col items-center mt-10 space-y-6 w-full max-w-lg">
        <Button onClick={handleSelectClick}>Select PDF Files</Button>
        <p className="text-sm text-gray-200">
          Accepted: PDF only • Max {MAX_FILES} files • Max {MAX_FILE_SIZE / (1024 * 1024)}MB each
        </p>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          multiple
          className="hidden"
        />

        {selectedFiles.length > 0 && (
          <div className="mt-6 w-full max-w-md bg-white text-gray-800 rounded-xl p-4 shadow-lg">
            <h2 className="font-semibold mb-2">Files ready to upload:</h2>
            <ul className="space-y-1">
              {selectedFiles.map((file, index) => (
                <li
                  key={index}
                  className="flex justify-between items-center border border-gray-300 rounded-md p-2"
                >
                  <span>
                    {file.name} ({Math.round(file.size / 1024)} KB)
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
            <Button onClick={handleUploadAndProcess} className="mt-4" disabled={processing}>
              {processing ? "Uploading & Processing..." : "Upload & Process"}
            </Button>
            {message && <p className="mt-2 text-sm">{message}</p>}
          </div>
        )}
      </div>
    </main>
  );
}
