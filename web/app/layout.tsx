import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { REPO_URL } from "../lib/measures";

export const metadata: Metadata = {
  title: {
    default: "GTA Housing Pipeline",
    template: "%s — GTA Housing Pipeline",
  },
  description:
    "A production-shaped data platform over GTA municipal housing data: ingested, modelled, and served with every number traceable to its rows.",
};

const NAV: Array<{ href: string; label: string }> = [
  { href: "/ask", label: "Ask" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/evals", label: "Evals" },
  { href: "/architecture", label: "Architecture" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <header className="site-header">
          <div className="container">
            <a className="wordmark" href="/">
              GTA Housing Pipeline
            </a>
            <nav className="site-nav" aria-label="Primary">
              {NAV.map((item) => (
                <a key={item.href} href={item.href}>
                  {item.label}
                </a>
              ))}
              <a href={REPO_URL} rel="noopener">
                GitHub
              </a>
            </nav>
          </div>
        </header>
        <main id="main">
          <div className="container">{children}</div>
        </main>
        <footer className="site-footer">
          <div className="container">
            <ul>
              <li>
                <a href={REPO_URL} rel="noopener">
                  Repository
                </a>
              </li>
              <li>
                <a href={`${REPO_URL}/blob/main/LICENSE`} rel="noopener">
                  MIT licence
                </a>
              </li>
              <li>
                <a href={`${REPO_URL}/tree/main/docs/sources`} rel="noopener">
                  Data sources
                </a>
              </li>
              <li>
                Toronto Open Government Licence · Mississauga Terms of Use ·
                Brampton CC BY · Peel Licence v1.0 · Statistics Canada Open
                Licence
              </li>
            </ul>
          </div>
        </footer>
      </body>
    </html>
  );
}
