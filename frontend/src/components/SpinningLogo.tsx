"use client";
import React from "react";

interface SpinningLogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const SpinningLogo: React.FC<SpinningLogoProps> = ({ 
  size = "md", 
  className = "" 
}) => {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-12 h-12", 
    lg: "w-16 h-16"
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div 
        className={`${sizeClasses[size]} border-4 border-white border-t-transparent rounded-full animate-spin`}
        style={{ animationDuration: "1s" }}
      />
    </div>
  );
};
