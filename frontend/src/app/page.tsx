"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { getFirebaseApp } from "@/services/firebase";
import { getAuth, onAuthStateChanged } from "firebase/auth";

// ─── detect auth ──────────────────────────────────────────────────────────────
function useAuth() {
  const [user, setUser] = useState<any>(undefined);
  useEffect(() => {
    const app = getFirebaseApp();
    const auth = getAuth(app);
    return onAuthStateChanged(auth, (u) => setUser(u ?? null));
  }, []);
  return user;
}

// ─── Jelly button ─────────────────────────────────────────────────────────────
function JellyButton({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  const [jelly, setJelly] = useState(false);
  return (
    <button
      className={`hero-btn ${jelly ? "jelly-active" : ""}`}
      onClick={onClick}
      onMouseEnter={() => { setJelly(false); requestAnimationFrame(() => setJelly(true)); }}
      onAnimationEnd={() => setJelly(false)}
    >
      {children}
    </button>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Home() {
  const user = useAuth();
  const router = useRouter();

  return (
    <>
      {/* ── Google Fonts ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&family=Reenie+Beanie&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #fafafa; }

        .hero-grain::after {
          content: '';
          position: absolute; inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
          pointer-events: none; z-index: 1; border-radius: inherit;
        }

        .hero-btn {
          display: inline-flex; align-items: center;
          padding: 0.9rem 2.2rem;
          background: linear-gradient(135deg, #fe2c55, #ff6b35);
          color: #fff; border: none; border-radius: 50px;
          font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem;
          cursor: pointer; letter-spacing: 0.02em;
          box-shadow: 0 4px 24px rgba(254,44,85,0.3);
          position: relative; z-index: 2;
          animation: jelly-idle 3s ease-in-out infinite;
          transition: box-shadow 0.2s ease;
        }
        .hero-btn:hover {
          box-shadow: 0 8px 40px rgba(254,44,85,0.45);
        }
        .jelly-active {
          animation: jelly-squish 1s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
        }

        @keyframes jelly-idle {
          0%, 100% { border-radius: 50px; }
          25%  { border-radius: 60px 40px 55px 45px / 45px 55px 40px 60px; }
          50%  { border-radius: 45px 55px 40px 60px / 60px 40px 55px 45px; }
          75%  { border-radius: 55px 45px 60px 40px / 40px 60px 45px 55px; }
        }

        .flow-pill {
          display: flex; align-items: center; justify-content: center;
          flex-direction: column;
          padding: 1.5rem 1.25rem;
          gap: 0.6rem;
          min-width: 120px;
          transition: transform 0.3s;
        }
        .flow-pill:hover { transform: translateY(-4px); }

        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .fade-up { animation: fadeUp 0.7s ease forwards; opacity: 0; }
      `}</style>

        <main style={{ background: "linear-gradient(135deg, #fff5f5 0%, #fafafa 50%, #f0fffe 100%)", color: "#111", minHeight: "100vh", fontFamily: "'DM Sans', sans-serif", overflowX: "hidden" }}>
        {/* ──────────────── HERO ──────────────── */}
        <section style={{ position: "relative", minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "8rem 1.5rem 4rem" }} className="hero-grain">

          {/* Headline */}
          <h1 className="fade-up" style={{
            animationDelay: "0.15s",
            fontFamily: "'Reenie Beanie', cursive",
            fontSize: "clamp(6rem, 8vw, 7rem)",
            lineHeight: 1.05,
            letterSpacing: "-0.03em",
            fontWeight: 800,
            color: "#111",
          }}>
            Your Notes,<br />
            <span style={{
              background: "linear-gradient(135deg, #fe2c55 0%, #ff6b35 35%, #25f4ee 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}>Now Addictive.</span>
          </h1>

          {/* Subheading */}
          <p className="fade-up" style={{
            animationDelay: "0.3s",
            color: "#777",
            fontSize: "clamp(1rem, 2vw, 1.25rem)",
            lineHeight: 1.7,
            maxWidth: 480,
            margin: "1.5rem auto 2.5rem",
            position: "relative", zIndex: 2,
          }}>
            Upload a PDF or lecture video. TikTalk turns it into short-form clips in minutes.
          </p>

          {/* Upload button */}
          <div className="fade-up" style={{ animationDelay: "0.45s", position: "relative", zIndex: 2 }}>
            <JellyButton onClick={() => router.push(user ? "/create" : "/login")}>
              Get Started
            </JellyButton>
          </div>

            {/* Flow diagram */}
            <div className="fade-up" style={{
              animationDelay: "0.6s",
              display: "flex", alignItems: "center", gap: "0.5rem",
              marginTop: "4.5rem", flexWrap: "wrap", justifyContent: "center",
              position: "relative", zIndex: 2,
              background: "#ffffff",
              border: "1px solid rgba(0,0,0,0.07)",
              boxShadow: "0 2px 20px rgba(0,0,0,0.06)",
              borderRadius: "24px",
              padding: "1rem 2rem",
            }}>
            {[
              { src: "/pdfimg.png", label: "PDF", color: "#fe2c55" },
              { src: "/mp4img.png", label: "MP4 / MP3", color: "#ff6b35" },
            ].map((item) => (
              <div key={item.label} className="flow-pill">
                <div style={{ width: 56, height: 56, position: "relative" }}>
                  <Image src={item.src} alt={item.label} fill style={{ objectFit: "contain" }} />
                </div>
                <span style={{ fontSize: "0.78rem", color: item.color, fontWeight: 600, letterSpacing: "0.08em" }}>{item.label}</span>
              </div>
            ))}

            {/* Arrow */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.2rem" }}>
              <svg width="44" height="14" viewBox="0 0 48 16" fill="none">
                <path d="M0 8h40M34 2l8 6-8 6" stroke="url(#ag)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <defs>
                  <linearGradient id="ag" x1="0" y1="8" x2="48" y2="8" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#fe2c55"/><stop offset="1" stopColor="#25f4ee"/>
                  </linearGradient>
                </defs>
              </svg>
              <span style={{ fontSize: "0.6rem", color: "#bbb", letterSpacing: "0.1em", textTransform: "uppercase" }}>generates</span>
            </div>

            {/* TikTalk */}
            <div className="flow-pill">
              <Image src="/ttlogo.png" alt="TikTalk" width={48} height={48} style={{ borderRadius: "50%" }} />
              <span style={{ fontSize: "0.78rem", color: "#0a9e99", fontWeight: 700, letterSpacing: "0.08em" }}>TIKTALK</span>
            </div>
          </div>
        </section>

        {/* ──────────────── FOOTER ──────────────── */}
        <footer style={{ borderTop: "1px solid rgba(0,0,0,0.08)", padding: "2rem 1.5rem", display: "flex", justifyContent: "center", alignItems: "center" }}>
          <span style={{ color: "#aaa", fontSize: "0.8rem" }}>© 2025 TikTalk</span>
        </footer>

      </main>
    </>
  );
}