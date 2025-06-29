// app/layout.tsx
import "./globals.css";
import "./papyrus.css";
import { ReactNode } from "react";
import Header from "../components/Header";

export const metadata = {
  title: "Ki Wellness",
  description: "Your AI-powered wellness companion",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-green-100 text-gray-800 font-sans">
        <Header />
        {children}
        <footer className="text-center text-sm py-6 bg-green-50 text-green-800 mt-20">
          &copy; 2025 Ki Wellness LLC. All rights reserved.
        </footer>
      </body>
    </html>
  );
}
