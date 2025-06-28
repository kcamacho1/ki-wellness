"use client";
import { supabase } from "@/lib/supabaseClient";

export default function SignOutButton() {
  return (
    <button
      onClick={() => supabase.auth.signOut()}
      className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
    >
      Sign Out
    </button>
  );
}
