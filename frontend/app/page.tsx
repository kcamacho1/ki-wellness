// app/page.tsx
import Link from 'next/link';
import './papyrus.css';

export default function Home() {
  return (
    <main className="min-h-screen bg-[aliceblue] text-gray-800 font-sans">
      {/* Hero Section */}
      <section className="text-center py-24 px-6 bg-gradient-to-r from-green-100 to-teal-500 text-gray-600">
        
        <p className="text-lg md:text-xl text-gray-700 mb-6 max-w-2xl mx-auto">The Ki to Rebranding Your Health</p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link href="/pricing" className="bg-green-200 text-gray-700 font-semibold px-6 py-3 rounded-full shadow hover:bg-green-100 transition">
            Book One on One
          </Link>
          <Link href="/dashboard" className="bg-green-500 text-gray-700 font-semibold px-6 py-3 rounded-full hover:bg-green-100 transition">
            Use AI Assistant
          </Link>
        </div>
      </section>
    </main>
  );
}
