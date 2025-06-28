"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import type { User } from "@supabase/supabase-js"; // Use the right import


export default function LoginPage() {
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const router = useRouter();

  useEffect(() => {
    const init = async () => {
      const { data: sessionData } = await supabase.auth.getSession();
      setUser(sessionData.session?.user ?? null);
    };
    init();

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session) router.push("/dashboard");
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, [router]);

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({ provider: "google" });
  };

  const signInWithEmail = async () => {
    if (!email) return alert("Please enter an email.");
    const { error } = await supabase.auth.signInWithOtp({ email });
    if (error) {
      console.error(error);
      alert("Error sending magic link.");
    } else {
      alert("Check your email for a magic link to log in.");
    }
  };

  if (user) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center bg-green-50 space-y-4">
        <p className="text-green-800 font-semibold">Signed in as {user.email}</p>
        <button
          onClick={() => supabase.auth.signOut()}
          className="bg-green-700 text-white px-4 py-2 rounded hover:bg-green-800 transition"
        >
          Sign Out
        </button>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6 space-y-8 flex flex-col items-center">
      {/* Blurb */}
      <section className="max-w-xl text-center space-y-3">
        <h1 className="text-4xl font-bold text-green-800 papyrus">🌿 Welcome to Ki Wellness</h1>
        <p className="text-lg">
          Join a growing community committed to holistic health, nutrition, and self-care. 
          Your personal dashboard helps you track meals, discover inspiring content, and
          build lifelong habits.
        </p>
      </section>

      {/* Video Embed */}
      <div className="max-w-xl w-full aspect-w-16 aspect-h-9 rounded overflow-hidden shadow">
        <iframe
          src="https://www.youtube.com/embed/dQw4w9WgXcQ"
          title="Ki Wellness Intro"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="w-full h-full"
        />
      </div>

      {/* Auth Options */}
      <section className="max-w-md w-full bg-white p-6 rounded shadow space-y-4">
        <button
          onClick={signInWithGoogle}
          className="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700 transition"
        >
          Continue with Google
        </button>
        <div className="flex items-center space-x-2">
          <hr className="flex-grow border-gray-300" />
          <span className="text-sm text-gray-500">or</span>
          <hr className="flex-grow border-gray-300" />
        </div>
        <div className="flex space-x-2">
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="flex-grow border border-gray-300 rounded px-3 py-2"
          />
          <button
            onClick={signInWithEmail}
            className="bg-green-700 text-white px-4 py-2 rounded hover:bg-green-800 transition"
          >
            Email Link
          </button>
        </div>
        <p className="text-xs text-gray-500 text-center">
          No spam. Sign in securely with Google or receive a magic link by email.
        </p>
      </section>
    </main>
  );
}
