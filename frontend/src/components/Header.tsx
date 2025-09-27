import React from "react";

type HeaderParams = {
    headerText: string;
    subtext?: string;
}

export function Header({ headerText, subtext=""}: HeaderParams) {
    return (
        <header>
            <h1 className="text-5xl font-bold mb-6">{headerText}</h1>
            <p className="text-lg items-center justify-center mb-10 max-w-xl mx-auto">
                {subtext}
            </p>
        
        </header>
    );
}