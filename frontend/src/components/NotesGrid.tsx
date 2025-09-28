"use client";
import React from "react";
import { useRouter } from "next/navigation";

interface Note {
  id: number;
  firebase_uid: string;
  title: string;
  notes_link: string;
  status: string;
  videos_link: string | null;
  created_at: string;
}

interface NotesGridProps {
  notes: Note[];
  loading: boolean;
  error: string | null;
}

export const NotesGrid: React.FC<NotesGridProps> = ({ notes, loading, error }) => {
  const router = useRouter();

  const handleNoteClick = (noteId: number) => {
    router.push(`/videos/${noteId}`);
  };

  const getVideoCount = (videosLink: string | null) => {
    if (!videosLink) return 0;
    return videosLink.split(',').length;
  };

  const getFirstVideoUrl = (videosLink: string | null) => {
    if (!videosLink) return null;
    return videosLink.split(',')[0].trim();
  };

  const formatDate = (dateString: string) => {
    if (!dateString) {
      return 'Unknown Date';
    }
    
    const date = new Date(dateString);
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'started':
        return 'bg-yellow-500';
      case 'not_started':
        return 'bg-gray-500';
      default:
        return 'bg-blue-500';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-200 text-lg">{error}</p>
      </div>
    );
  }

  if (notes.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-300 text-lg">No notes found. Upload some files to get started!</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 w-full max-w-7xl">
      {notes.map((note) => {
        const videoCount = getVideoCount(note.videos_link);
        const firstVideoUrl = getFirstVideoUrl(note.videos_link);
        
        return (
          <div
            key={note.id}
            onClick={() => handleNoteClick(note.id)}
            className="bg-white rounded-lg shadow-lg overflow-hidden cursor-pointer transform transition duration-300 hover:scale-105 hover:shadow-2xl"
          >
            {/* Video Preview */}
            <div className="aspect-video bg-gray-200 relative">
              {firstVideoUrl && note.status === 'completed' ? (
                <video
                  className="w-full h-full object-cover"
                  preload="metadata"
                  muted
                >
                  <source src={firstVideoUrl} type="video/mp4" />
                </video>
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-400 to-purple-500">
                  <div className="text-center text-white">
                    <div className="text-4xl mb-2">🎬</div>
                    <div className="text-sm font-semibold">
                      {note.status === 'completed' ? 'Video Ready' : 'Processing...'}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Status Badge */}
              <div className="absolute top-2 right-2">
                <span className={`px-2 py-1 rounded-full text-xs font-semibold text-white ${getStatusColor(note.status)}`}>
                  {note.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              
              {/* Video Count Badge */}
              {videoCount > 0 && (
                <div className="absolute bottom-2 right-2">
                  <span className="bg-black bg-opacity-70 text-white px-2 py-1 rounded-full text-xs font-semibold">
                    {videoCount} video{videoCount > 1 ? 's' : ''}
                  </span>
                </div>
              )}
            </div>
            
            {/* Note Info */}
            <div className="p-4">
              <h3 className="font-semibold text-gray-800 mb-1 line-clamp-2">
                {note.title}
              </h3>
              <p className="text-sm text-gray-600 mb-2">
                Created {formatDate(note.created_at)}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {note.status === 'completed' ? 'Ready to view' : 'Processing...'}
                </span>
                <div className="text-blue-600 text-sm font-medium">
                  View →
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
