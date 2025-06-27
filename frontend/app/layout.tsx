// app/layout.tsx
import './globals.css';
import './papyrus.css';
import Link from 'next/link';
import type { Metadata } from 'next';
import Image from 'next/image';


export const metadata: Metadata = {
  title: 'Ki Wellness',
  description: 'AI-powered holistic wellness support',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-green-100 text-gray-800 font-sans">
        <header className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center p-6">
          <div className="flex items-center space-x-4">

            <Link href="/" className="hover:underline">
              <Image src="/logoname.png" alt="Ki Wellness Logo" width={180} height={60} className="rounded" />
            </Link>
          </div>
          <nav className="flex gap-4 text-green-900 text-sm md:text-base font-medium mt-4 md:mt-0">
            <Link href="/about" className="hover:underline">About</Link>
            <Link href="/pricing" className="hover:underline">Services & Pricing</Link>
            <Link href="/coming-soon" className="hover:underline">AI Assistant</Link>
            <Link href="/resources" className="hover:underline">Free Resources</Link>
          </nav>
        </header>

        {children}

        <footer className="text-center text-sm py-6 bg-green-50 text-green-800 mt-20">
          &copy; 2025 Ki Wellness LLC. All rights reserved.
        </footer>
      </body>
    </html>
  );
}
