"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import type { User } from "@supabase/auth-js";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6 space-y-8 relative">

      {/* Header */}
      <section className="max-w-6xl mx-auto text-center bg-white p-6 rounded-lg shadow">
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-2">
          🌿 Your Dashboard
        </h1>
        <p className="text-lg text-gray-700">
          Track your progress, log meals and workouts, and stay inspired.
        </p>
      </section>


      {/* Quick Stats */}
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            title: "Meals Logged",
            count: "12",
            desc: "Meals tracked this week",
          },
          {
            title: "Workouts",
            count: "4",
            desc: "Workouts completed",
          },
          {
            title: "Mindful Sessions",
            count: "3",
            desc: "Meditation & self-care",
          },
        ].map(({ title, count, desc }) => (
          <div
            key={title}
            className="bg-white border border-green-200 rounded-lg shadow p-4 flex flex-col items-center text-center space-y-2 hover:shadow-md transition"
          >
            <h3 className="text-xl font-bold text-green-800 papyrus">{title}</h3>
            <p className="text-3xl font-bold">{count}</p>
            <p className="text-sm text-gray-700">{desc}</p>
          </div>
        ))}
      </section>

      {/* Quick Actions */}
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "➕ Log a Meal", href: "/food-journal" },
          { label: "➕ Log a Workout", href: "/exercise" },
          { label: "✨ See Recommendations", href: "/recommendations" },
        ].map(({ label, href }) => (
          <Link
            key={label}
            href={href}
            className="bg-white border border-green-200 rounded-lg shadow p-6 text-center hover:bg-green-50 transition flex items-center justify-center font-semibold text-green-800"
          >
            {label}
          </Link>
        ))}
      </section>

      {/* Motivation Section */}
      <section className="max-w-6xl mx-auto bg-white p-6 rounded-lg shadow text-center">
        <h2 className="text-2xl font-bold text-green-800 papyrus mb-2">
          🌱 Keep Going!
        </h2>
        <p className="text-lg text-gray-700">
          Every small action adds up to big changes. You’re doing great.
        </p>
      </section>
    </main>
  );
}
