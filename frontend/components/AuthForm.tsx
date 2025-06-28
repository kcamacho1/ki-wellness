"use client";
import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";

export default function AuthForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSignUp() {
    setLoading(true);
    setError("");
    const { error } = await supabase.auth.signUp({
      email,
      password,
    });
    if (error) setError(error.message);
    setLoading(false);
  }

  async function handleSignIn() {
    setLoading(true);
    setError("");
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) setError(error.message);
    setLoading(false);
  }

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded shadow space-y-4">
      <h2 className="text-xl font-bold text-center text-green-800">
        Sign Up / Sign In
      </h2>
      {error && <p className="text-red-600 text-center">{error}</p>}
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
      <button
        onClick={handleSignUp}
        disabled={loading}
        className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
      >
        {loading ? "Loading..." : "Sign Up"}
      </button>
      <button
        onClick={handleSignIn}
        disabled={loading}
        className="w-full bg-gray-600 text-white py-2 rounded hover:bg-gray-700 transition"
      >
        {loading ? "Loading..." : "Sign In"}
      </button>
    </div>
  );
}
