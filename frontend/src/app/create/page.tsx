"use client";

import React, { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Button } from "@/components/Button";
import { SpinningLogo } from "@/components/SpinningLogo";
import { useFirebaseAuth } from "@/hooks/useFirebaseAuth";
import { onAuthStateChanged, User } from "firebase/auth";

const gradientBg = "linear-gradient(135deg, #fe2c55 0%, #ff6b35 50%, #25f4ee 100%)";
const MAX_FILES = 5;

export default function Upload() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [title, setTitle] = useState("");
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [currentNotesId, setCurrentNotesId] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const auth = useFirebaseAuth();

  // Listen for auth state changes
  useEffect(() => {
    if (auth) {
      const unsubscribe = onAuthStateChanged(auth, (user) => setUser(user));
      return () => unsubscribe();
    }
  }, [auth]);

  // Cleanup polling interval on unmount
  useEffect(() => () => { if (pollingInterval) clearInterval(pollingInterval); }, [pollingInterval]);

  // Poll notes status
  const pollNotesStatus = async (notesId: number) => {
    if (!user) return;
    try {
      const token = await user.getIdToken();
      const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/notes/${notesId}`;
      console.log("[Polling] GET", url);
      const response = await fetch(url, { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } });
      console.log("[Polling] Status:", response.status);
      let data: any = null;
      try { data = await response.json(); console.log("[Polling] Response JSON:", JSON.stringify(data, null, 2)); }
      catch (err) { console.error("[Polling] Failed to parse JSON:", err); }
      if (response.ok && data) {
        const notes = data.notes;
        setStatus(notes.status);
        if (notes.status === "completed") {
          console.log("Notes completed, redirecting...");
          if (pollingInterval) { clearInterval(pollingInterval); setPollingInterval(null); }
          setProcessing(false);
          router.push(`/videos/${notesId}`);
        } else { console.log("⏳ Not completed yet:", notes.status); }
      } else {
        console.error("[Polling] Error Response:", response.status, data);
        setMessage(`API Error: ${response.status} - ${data?.error || "Unknown error"}`);
      }
    } catch (error) { console.error("[Polling] Exception:", error); setMessage(`Network Error: ${error}`); }
  };

  // Start polling when notes ID is set
  useEffect(() => {
    if (currentNotesId && !pollingInterval) {
      console.log("▶️ Starting polling for notes", currentNotesId);
      console.log("▶️ API Base URL:", process.env.NEXT_PUBLIC_API_BASE_URL);
      const interval = setInterval(() => pollNotesStatus(currentNotesId), 5000);
      setPollingInterval(interval);
    }
  }, [currentNotesId, pollingInterval, user]);

  // Reset state
  const resetState = () => {
    console.log("Resetting state");
    setCurrentNotesId(null); setStatus(""); setMessage(""); setTitle("");
    setSelectedFiles([]); setProcessing(false);
    if (pollingInterval) { clearInterval(pollingInterval); setPollingInterval(null); }
  };

  const handleSelectClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const supportedTypes = ["application/pdf","video/mp4","video/quicktime","video/x-msvideo","audio/mpeg","audio/wav","audio/mp4","audio/x-m4a"];
    const validFiles = Array.from(e.target.files).filter((file) => {
      if (!supportedTypes.includes(file.type)) { alert(`${file.name} is not supported. Supported: PDF, MP4, MP3, WAV, M4A`); return false; }
      return true;
    });
    if (validFiles.length + selectedFiles.length > MAX_FILES) { alert(`You can only upload up to ${MAX_FILES} files.`); return; }
    setSelectedFiles((prev) => [...prev, ...validFiles]);
  };

  const handleRemoveFile = (index: number) => setSelectedFiles((prev) => prev.filter((_, i) => i !== index));

  const handleUploadAndProcess = async () => {
    if (!title.trim()) { setMessage("Please enter a title for your video set."); return; }
    setProcessing(true); setMessage("");
    try {
      const uploadedUrls: string[] = [];
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append("file", file);
        console.log("[Upload] POST /api/upload", file.name);
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        console.log("[Upload] Status:", res.status);
        try { const data = await res.json(); console.log("[Upload] Response:", data); if (res.ok && data.url) uploadedUrls.push(data.url); }
        catch (err) { console.error("[Upload] Failed to parse JSON:", err); }
      }
      if (!user) { setMessage("You must be logged in to continue."); setProcessing(false); return; }
      const token = await user.getIdToken();
      const apiUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/files/process-files`;
      if (uploadedUrls.length > 0) {
        console.log("[Process] POST", apiUrl);
        const res2 = await fetch(apiUrl, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify({ title: title.trim(), file_urls: uploadedUrls }),
        });
        console.log("[Process] Status:", res2.status);
        let json: any = null;
        try { json = await res2.json(); console.log("[Process] Response JSON:", json); }
        catch (err) { console.error("[Process] Failed to parse JSON:", err); }
        if (res2.ok && json?.notes?.id) { setMessage("Processing started successfully."); setCurrentNotesId(json.notes.id); setStatus("not_started"); }
        else { setMessage(json?.error || "Failed to start processing."); setProcessing(false); }
      }
    } catch (err) { console.error("[Upload/Process] Exception:", err); setMessage("Unexpected error occurred."); setProcessing(false); }
  };

  // --- Render ---
  if (!auth) return (
    <main className="relative flex flex-col items-center justify-center min-h-screen text-white px-4" style={{ background: gradientBg }}>
      <Header headerText="Upload Files" />
      <p>Loading...</p>
    </main>
  );

  if (!user) return (
    <main className="relative flex flex-col min-h-screen text-white px-4" style={{ background: gradientBg }}>
      <Header headerText="Upload Files" />
      <div className="flex flex-col items-center justify-center flex-1 gap-4 text-center">
        <h1 className="text-6xl font-bold">Upload Files</h1>
        <p className="text-xl">You must be logged in to upload files.</p>
        <button onClick={() => (window.location.href = "/login")} className="px-8 py-3 rounded-full font-semibold text-white hover:opacity-90 transition" style={{ background: "#0f0f0f" }}>
          Go to Login
        </button>
      </div>
    </main>
  );

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen text-white px-4 overflow-hidden" style={{ background: gradientBg }}>
      <Header headerText="Upload Files" />

      <div className="relative z-10 flex flex-col items-center mt-16 space-y-8 w-full max-w-xl">

        {/* Title Input Panel */}
        <div className="w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8">
          <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-3">Video Set Title</label>
          <input
            id="title" type="text" value={title} onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a title for your video set..."
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#fe2c55] transition"
            disabled={processing} maxLength={100}
          />
          <p className="text-xs text-gray-500 mt-2 text-right">{title.length}/100</p>
        </div>

        {/* Upload Area */}
        {!processing && (
          <div className="w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-10 text-center transition hover:border-[#fe2c55]/40">
            <div className="mb-6">
              <p className="text-lg font-semibold">Drag & drop files here</p>
              <p className="text-sm text-gray-400 mt-2">or click below to select</p>
            </div>
            <button onClick={handleSelectClick} disabled={processing} className="px-8 py-3 rounded-full font-semibold bg-gradient-to-br from-[#fe2c55] to-[#ff6b35] hover:scale-105 transition-transform shadow-[0_0_30px_rgba(254,44,85,0.4)]">
              Select Files
            </button>
            <p className="text-xs text-gray-500 mt-6">Accepted: PDF, MP4, MP3, WAV, M4A • Max {MAX_FILES} files</p>
          </div>
        )}

        {/* Hidden File Input */}
        <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".pdf,.mp4,.mp3,.wav,.m4a,.mov,.mkv" multiple className="hidden" disabled={processing} />

        {/* Processing State */}
        {processing && (
          <div className="w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-10 flex flex-col items-center space-y-6">
            <SpinningLogo size="lg" />
            <div className="text-center">
              <p className="text-lg font-semibold">Generating Clips...</p>
              <p className="text-sm text-gray-400 mt-2">Status: {status || "Starting..."}</p>
              {currentNotesId && <p className="text-xs text-gray-500 mt-1">Notes ID: {currentNotesId}</p>}
            </div>
            <button onClick={resetState} className="px-6 py-2 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 transition text-sm">Cancel</button>
          </div>
        )}

        {/* Selected Files List */}
        {selectedFiles.length > 0 && !processing && (
          <div className="w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8">
            <h2 className="font-semibold mb-4">Files Ready</h2>
            <ul className="space-y-3">
              {selectedFiles.map((file, index) => (
                <li key={index} className="flex justify-between items-center border border-white/10 rounded-xl px-4 py-2 bg-white/5">
                  <span className="text-sm truncate max-w-[70%]">{file.name}</span>
                  <button onClick={() => handleRemoveFile(index)} className="text-red-400 hover:text-red-500 font-bold">✕</button>
                </li>
              ))}
            </ul>
            <button onClick={handleUploadAndProcess} disabled={processing} className="mt-6 w-full py-3 rounded-full font-semibold bg-gradient-to-br from-[#fe2c55] to-[#ff6b35] hover:scale-105 transition-transform shadow-[0_0_30px_rgba(254,44,85,0.4)]">
              Upload & Generate
            </button>
            {message && <p className="mt-4 text-sm text-gray-400">{message}</p>}
          </div>
        )}

      </div>
    </main>
  );
}