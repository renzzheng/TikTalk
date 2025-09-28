"use client";
import React from "react";

type ButtonParams = {
    children: React.ReactNode;
    onClick?: () => void;
    className?: string;
    disabled?: boolean;
}

export function Button({ children, onClick, className = "", disabled = false }: ButtonParams) {
    return (
        <button
      onClick={onClick}
      disabled={disabled}
      className={`px-6 py-3 bg-white text-indigo-600 font-semibold rounded-2xl shadow-md hover:bg-gray-200 transition ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
    );
}