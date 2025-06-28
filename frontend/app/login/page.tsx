"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import AuthForm from "@/components/AuthForm";
import SignOutButton from "@/components/SignOutButton";

export default function LoginPage() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const session = supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
    });

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  if (!user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-green-50">
        <AuthForm />
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-green-50 space-y-4">
      <p className="text-green-800 font-semibold">Signed in as {user.email}</p>
      <SignOutButton />
    </main>
  );
}
