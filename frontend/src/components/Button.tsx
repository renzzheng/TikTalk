"use client";
import React from "react";

type ButtonParams = {
    children: React.ReactNode;
    onClick?: () => void;
    className?: string;
}

export function Button({ children, onClick, className = "" }: ButtonParams) {
    return (
        <button
      onClick={onClick}
      className={`px-6 py-3 bg-white text-indigo-600 font-semibold rounded-2xl shadow-md hover:bg-gray-200 transition ${className}`}
    >
      {children}
    </button>
    );
}