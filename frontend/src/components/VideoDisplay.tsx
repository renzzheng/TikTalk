"use client";
import React from "react";

interface VideoDisplayProps {
  videoUrls: string[];
  onBack: () => void;
}

export const VideoDisplay: React.FC<VideoDisplayProps> = ({ videoUrls, onBack }) => {
  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-white">Your Generated Videos</h1>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition-colors"
        >
          Upload More
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {videoUrls.map((url, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="aspect-video bg-gray-200">
              <video
                controls
                className="w-full h-full object-cover"
                preload="metadata"
              >
                <source src={url} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-gray-800 mb-2">
                Video {index + 1}
              </h3>
              <div className="flex space-x-2">
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                >
                  Open
                </a>
                <button
                  onClick={() => navigator.clipboard.writeText(url)}
                  className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                >
                  Copy Link
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {videoUrls.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-300 text-lg">No videos generated yet.</p>
        </div>
      )}
    </div>
  );
};
