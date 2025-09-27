"use client";

import * as NavigationMenu from "@radix-ui/react-navigation-menu";
import Link from "next/link";
import Image from "next/image";

export function Navbar() {
    return (
        <nav className="w-full bg-gray-900 text-white shadow-md">
            <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
                <Link href="/" className="flex items-center space-x-2">
                    <Image
                        src="/ttlogo.png" // place logo.svg or logo.png inside /public
                        alt="App Logo"
                        width={60}
                        height={60}
                        className="h-15 w-15 rounded-full"
                        priority
                    />
                </Link>
                <NavigationMenu.Root>
                    <NavigationMenu.List className="flex space-x-6">

                        <NavigationMenu.Item>
                            <NavigationMenu.Link asChild>
                                <Link
                                    href="/"
                                    className="px-4 py-2 rounded-md hover:bg-gray-700 transition"
                                >
                                    Home
                                </Link>
                            </NavigationMenu.Link>
                        </NavigationMenu.Item>

                        <NavigationMenu.Item>
                            <NavigationMenu.Link asChild>
                                <Link
                                    href="/upload"
                                    className="px-4 py-2 rounded-md hover:bg-indigo-600 bg-blue-500 transition"
                                >
                                    Upload
                                </Link>
                            </NavigationMenu.Link>
                        </NavigationMenu.Item>

                        <NavigationMenu.Item>
                            <NavigationMenu.Link asChild>
                                <Link
                                    href="/login"
                                    className="px-4 py-2 rounded-md hover:bg-indigo-600 bg-blue-500 transition"
                                >
                                    Log In
                                </Link>
                            </NavigationMenu.Link>
                        </NavigationMenu.Item>

                        <NavigationMenu.Item>
                            <NavigationMenu.Link asChild>
                                <Link
                                    href="/signup"
                                    className="px-4 py-2 rounded-md hover:bg-indigo-600 bg-blue-500 transition"
                                >
                                    Sign Up
                                </Link>
                            </NavigationMenu.Link>
                        </NavigationMenu.Item>

                    </NavigationMenu.List>
                </NavigationMenu.Root>
            </div>
        </nav>
    );
}
