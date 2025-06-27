"use client";
// app/coming-soon/page.tsx
import { useState, useEffect } from "react";

const tips: string[] = [
  "🌿 Drink a glass of water before every meal to improve digestion.",
  "🧘‍♀️ Take 5 deep breaths to reset your mind.",
  "🏃‍♂️ A 10-minute walk can boost your mood and energy.",
  "💤 Prioritize 7-8 hours of quality sleep each night.",
  "🍎 Add colorful veggies to your meals for more nutrients.",
  "🙏 Practice gratitude: Write down 3 things you’re thankful for.",
  "✨ Visualize your goals for 5 minutes every morning.",
  "🥗 Eat mindfully and slow down to savor each bite.",
  "📵 Take a digital detox break for 30 minutes today.",
  "💪 Move your body in ways that feel joyful to you."
];

export default function DashboardPage() {
  const [randomTip, setRandomTip] = useState<string>("");

  useEffect(() => {
    const tip = tips[Math.floor(Math.random() * tips.length)];
    setRandomTip(tip);
  }, []); // <-- No need for [tips]

  return (
    <main className="min-h-screen bg-green-900 text-green-700 p-6 space-y-4 font-inter">
      <section className="max-w-6xl mx-auto bg-amber-50 p-6 rounded-xl shadow text-gray-800">
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-2">
          coming soon
        </h1>
        <p className="text-gray-700">
          Keep it Simple ~ Stay on Track ~ Journal your food, track your wellness, and analyze nutrition.
        </p>
      </section>

            {/* Coming Soon Section */}
      <section className="max-w-6xl mx-auto bg-amber-50 p-6 rounded-xl shadow text-gray-800 space-y-6">
         <div className="flex flex-col items-center">
          <h1 style={{ fontSize: "2rem", color: "#388e3c", marginBottom: "0.5em", fontFamily: "Papyrus" }}>
            Ki Wellness
            </h1>
            <p
              style={{
                fontStyle: "italic",
                color: "#555",
                marginBottom: "1.5em"
              }}
            >
              {randomTip}
            </p>
            <p style={{ fontWeight: "bold", marginBottom: "1em" }}>
            🌟 Submit your email for early access to our AI-powered nutrition tools.
            </p>
          </div>
        <form
          action="https://YOUR-MAILCHIMP-OR-FORM-ENDPOINT"
          method="POST"
          style={{ display: "flex", flexDirection: "column", alignItems: "center" }}
        >
          <input
            type="email"
            name="email"
            placeholder="Enter your email"
            required
            style={{
              padding: "0.75em",
              width: "80%",
              border: "1px solid #ccc",
              borderRadius: "4px",
              marginBottom: "1em",
              fontSize: "1em"
            }}
          />
          <button
            type="submit"
            style={{
              backgroundColor: "#43a047",
              color: "white",
              padding: "0.75em 1.5em",
              border: "none",
              borderRadius: "4px",
              fontSize: "1em",
              cursor: "pointer"
            }}
          >
            Notify Me
          </button>
        </form>
        <div
          style={{
            marginTop: "1em",
            fontSize: "0.85em",
            color: "#666"
          }}
        >
          No spam. Unsubscribe anytime.
        </div>  
      </section>
    </main>
  );
}



  