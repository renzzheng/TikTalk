import React from "react";

type HeaderParams = {
    headerText: string;
}

export function Header({ headerText }: HeaderParams) {
    return (
        <header>
            <h1 className="text-5xl font-bold mb-6">{headerText}</h1>
            <p className="text-lg items-center justify-center mb-10 max-w-xl mx-auto">
                Discover a new way to create, share, and connect. Our platform makes
                it simple and intuitive to get started.
            </p>
        
        </header>
    );
}