"use client";
import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";

export default function AuthForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleEmailSignIn = async (type: "signIn" | "signUp") => {
    setLoading(true);
    const fn =
      type === "signUp"
        ? supabase.auth.signUp
        : supabase.auth.signInWithPassword;

    const { error } = await fn({
      email,
      password,
    });

    if (error) {
      alert(error.message);
    } else {
      alert("Check your email for confirmation.");
    }

    setLoading(false);
  };

  const handleOAuthSignIn = async (provider: "google" | "apple") => {
    setLoading(true);
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
    });
    if (error) alert(error.message);
    setLoading(false);
  };

  return (
    <div className="w-full max-w-sm space-y-4">
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full border border-gray-300 rounded px-3 py-2"
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-full border border-gray-300 rounded px-3 py-2"
      />
      <div className="flex space-x-2">
        <button
          onClick={() => handleEmailSignIn("signIn")}
          className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 transition disabled:opacity-50"
          disabled={loading}
        >
          Log In
        </button>
        <button
          onClick={() => handleEmailSignIn("signUp")}
          className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 transition disabled:opacity-50"
          disabled={loading}
        >
          Sign Up
        </button>
      </div>

      <div className="flex items-center justify-center space-x-2">
        <button
          onClick={() => handleOAuthSignIn("google")}
          className="flex-1 bg-red-500 text-white py-2 rounded hover:bg-red-600 transition disabled:opacity-50"
          disabled={loading}
        >
          Sign in with Google
        </button>
        <button
          onClick={() => handleOAuthSignIn("apple")}
          className="flex-1 bg-black text-white py-2 rounded hover:bg-gray-800 transition disabled:opacity-50"
          disabled={loading}
        >
          Sign in with Apple
        </button>
      </div>
    </div>
  );
}
