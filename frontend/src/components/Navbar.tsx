"use client";

import * as NavigationMenu from "@radix-ui/react-navigation-menu";
import Link from "next/link";
import Image from "next/image";
import { isUserLoggedIn, signUserOut } from "@/hooks/useFirebaseAuth";

export function Navbar() {
  const isLoggedIn = isUserLoggedIn();

  const linkStyle = {
    display: "inline-block",
    padding: "0.45rem 1rem",
    borderRadius: "8px",
    color: "rgb(0, 0, 0)",
    textDecoration: "none",
    fontSize: "0.9rem",
    fontFamily: "'DM Sans', sans-serif",
    transition: "color 0.2s",
  };

  return (
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
      background: "rgba(250, 249, 249, 0.85)",
      backdropFilter: "blur(12px)",
      WebkitBackdropFilter: "blur(12px)",
      borderBottom: "1px solid rgba(37, 37, 37, 0.1)",
    }}>
      <div style={{ width: "100%", padding: "0.75rem 1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>

        {/* Logo — hugs left */}
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.6rem", textDecoration: "none" }}>
          <Image src="/ttlogo.png" alt="TikTalk" width={38} height={38} style={{ borderRadius: "50%" }} priority />
          <span style={{ fontWeight: 800, fontSize: "1.3rem", color: "#000" }}>TikTalk</span>
        </Link>

        {/* Nav links — hugs right */}
        <NavigationMenu.Root>
          <NavigationMenu.List style={{ display: "flex", alignItems: "center", gap: "0.25rem", listStyle: "none", margin: 0, padding: 0 }}>

            <NavigationMenu.Item>
              <NavigationMenu.Link asChild>
                <Link href="/" style={linkStyle}
                  onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(0, 0, 0)")}>
                  Home
                </Link>
              </NavigationMenu.Link>
            </NavigationMenu.Item>

            <NavigationMenu.Item>
              <NavigationMenu.Link asChild>
                <Link href="/create" style={linkStyle}
                  onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(0, 0, 0)")}>
                  Upload
                </Link>
              </NavigationMenu.Link>
            </NavigationMenu.Item>

            {!isLoggedIn && (
              <NavigationMenu.Item>
                <NavigationMenu.Link asChild>
                  <Link href="/login" style={linkStyle}
                    onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
                    onMouseLeave={e => (e.currentTarget.style.color = "rgba(0, 0, 0)")}>
                    Log In
                  </Link>
                </NavigationMenu.Link>
              </NavigationMenu.Item>
            )}

            {!isLoggedIn && (
              <NavigationMenu.Item>
                <NavigationMenu.Link asChild>
                  <Link href="/signup" style={linkStyle}
                    onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
                    onMouseLeave={e => (e.currentTarget.style.color = "rgba(0, 0, 0)")}>
                    Sign Up
                  </Link>
                </NavigationMenu.Link>
              </NavigationMenu.Item>
            )}

            {isLoggedIn && (
              <NavigationMenu.Item>
                <NavigationMenu.Link asChild>
                  <Link href="/login" onClick={signUserOut} style={linkStyle}
                    onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
                    onMouseLeave={e => (e.currentTarget.style.color = "rgba(51, 51, 51, 0.6)")}>
                    Sign Out
                  </Link>
                </NavigationMenu.Link>
              </NavigationMenu.Item>
            )}

          </NavigationMenu.List>
        </NavigationMenu.Root>
      </div>
    </nav>
  );
}