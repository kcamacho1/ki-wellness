"use client";
import { useState, useEffect } from "react";
import { supabase } from "../../lib/supabaseClient";

const tips: string[] = [
  "🌿 Drink a glass of water before every meal to improve digestion.",
  "🧘‍♀️ Take 5 deep breaths to reset your mind.",
  "🏃‍♂️ A 10-minute walk can boost your mood and energy.",
  "💤 Prioritize 7-8 hours of quality sleep each night.",
  "🍎 Eat colorful veggies for more nutrients.",
  "🙏 Practice gratitude: Write down 3 things you’re thankful for.",
  "✨ Visualize your goals for 5 minutes every morning.",
  "🥗 Eat mindfully and savor each bite.",
  "📵 Take a digital detox break for 30 minutes today.",
  "💪 Move your body in ways that feel joyful to you."
];

export default function ComingSoonPage() {
  const [randomTip, setRandomTip] = useState<string>("");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  useEffect(() => {
    const tip = tips[Math.floor(Math.random() * tips.length)];
    setRandomTip(tip);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");

    const { error } = await supabase
      .from("early_access_emails")
      .upsert(
        {
          email,
          unsubscribed: false,
          subscribed_at: new Date().toISOString(),
          unsubscribed_at: null
        },
        { onConflict: "email" }
      );

    if (error) {
      console.error(error);
      setStatus("error");
    } else {
      setStatus("success");
      setEmail("");
    }
  };

  return (
    <main className="min-h-screen bg-green-50 text-gray-800 p-6 flex flex-col items-center justify-center">
      <section className="max-w-2xl w-full bg-white p-8 rounded-lg shadow space-y-6 text-center">
        <h1 className="text-3xl font-bold text-green-800">Ki Wellness</h1>
        <p className="text-gray-700">
          Ki means life force—energy, movement, and the potential to thrive.
          It’s also the key to unlocking a healthier, more balanced life.
        </p>
        <p className="italic text-green-700">{randomTip}</p>
        <p className="text-gray-700">
          🌟 Sign up for early access to our AI-powered tools for nutrition, fitness, and spiritual well-being.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
          <input
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email"
            className="w-full border border-gray-300 rounded px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            type="submit"
            disabled={status === "submitting"}
            className="bg-green-600 text-white py-2 rounded hover:bg-green-700 transition disabled:opacity-50"
          >
            {status === "submitting" ? "Submitting..." : "Notify Me"}
          </button>
          {status === "success" && (
            <p className="text-green-700">✅ Thank you! You’re on the list.</p>
          )}
          {status === "error" && (
            <p className="text-red-600">⚠️ Something went wrong. Please try again.</p>
          )}
        </form>

        <p className="text-sm text-gray-500">
          No spam. Unsubscribe anytime.
        </p>
      </section>
    </main>
  );
}




  