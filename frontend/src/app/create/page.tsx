"use client";
import React, { useRef, useState } from "react";
import { Header } from "@/components/Header";
import { Button } from "@/components/Button";

export default function Upload() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleUploadClick = () => {
    // Open the file explorer
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles(files);

      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);

        try {
          const res = await fetch("/api/upload", {
            method: "POST",
            body: formData,
          });

          if (res.ok) {
            console.log(`${file.name} uploaded successfully!`);
          } else {
            console.error(`Failed to upload ${file.name}`);
          }
        } catch (err) {
          console.error(`Error uploading ${file.name}:`, err);
        }
      }
    }
  };

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4">
      <Header headerText="Upload your Video" />

      <div className="flex flex-col items-center justify-center text-center mt-10 space-y-4">
        <Button onClick={handleUploadClick}>Upload Files</Button>
        <p className="text-sm text-gray-200">
          Accepted file types: .pptx, .pdf, .mp4, .txt
        </p>

        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pptx,.pdf,.mp4,.txt"
          multiple
          className="hidden"
        />

        {/* Display uploaded files */}
        {selectedFiles.length > 0 && (
          <div className="mt-6 w-full max-w-md bg-white text-gray-800 rounded-xl p-4 shadow-lg">
            <h2 className="font-semibold mb-2">Files being processed:</h2>
            <ul className="space-y-1">
              {selectedFiles.map((file, index) => (
                <li
                  key={index}
                  className="border border-gray-300 rounded-md p-2 hover:bg-gray-100 transition"
                >
                  {file.name} ({Math.round(file.size / 1024)} KB)
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}