'use client';
import Link from 'next/link';

// app/pricing/page.tsx

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6">
      {/* Intro */}
      <section className="max-w-4xl mx-auto text-center mb-12">
        <h1 className="text-4xl font-bold text-green-800 mb-2 papyrus">
          🌿 Ki Wellness Pricing
        </h1>
        <p className="text-lg">
          Your Wellness, Your Way. Start free, grow at your own pace, and refill your cup anytime.
        </p>
      </section>

      {/* Subscription Tiers */}
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {/* Sprout Tier */}
        <div className="bg-white rounded-lg shadow p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-semibold mb-2">🌱 Sprout</h2>
            <p className="text-3xl font-bold mb-4">$0<span className="text-base font-normal">/month</span></p>
            <ul className="space-y-2 text-left text-gray-700 mb-6">
              <li>✅ 1 Month Food Journal</li>
              <li>✅ Free OpenFood Data</li>
              <li>✅ Save Playlists 7 Days</li>
              <li>✅ Share Recipes & Playlists</li>
              <li>❌ No AI Recommendations</li>
            </ul>
          </div>
          <button className="bg-green-600 text-white py-2 rounded hover:bg-green-700 transition">
            Sprout Free
          </button>
        </div>

        {/* Thrive Tier */}
        <div className="bg-white rounded-lg shadow p-6 border-2 border-green-600 flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-semibold mb-2">🌿 Thrive</h2>
            <p className="text-3xl font-bold mb-4">$2<span className="text-base font-normal">/month</span></p>
            <span className="inline-block bg-green-600 text-white text-xs px-2 py-1 rounded mb-4">
              Most Popular
            </span>
            <ul className="space-y-2 text-left text-gray-700 mb-6">
              <li>✅ Everything in Sprout</li>
              <li>✅ Nutritionix API Access</li>
              <li>✅ AI Recommendations</li>
              <li>✅ 30 Cups per Month</li>
              <li>✅ Extended Save & History</li>
            </ul>
          </div>
          <button className="bg-green-600 text-white py-2 rounded hover:bg-green-700 transition">
            Upgrade to Thrive
          </button>
        </div>

        {/* Flourish Tier */}
        <div className="bg-white rounded-lg shadow p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-semibold mb-2">🌳 Flourish</h2>
            <p className="text-3xl font-bold mb-4">$5<span className="text-base font-normal">/month</span></p>
            <ul className="space-y-2 text-left text-gray-700 mb-6">
              <li>✅ Everything in Thrive</li>
              <li>✅ 150 Cups per Month</li>
              <li>✅ Priority AI Processing</li>
              <li>✅ All Premium Features</li>
            </ul>
          </div>
          <button className="bg-green-600 text-white py-2 rounded hover:bg-green-700 transition">
            Upgrade to Flourish
          </button>
        </div>
      </section>

      {/* Pay-as-You-Go Cups */}
      <section className="max-w-4xl mx-auto text-center">
        <h2 className="text-2xl font-bold text-green-800 mb-4">
          💧 Refill Your Cup
        </h2>
        <p className="mb-6 text-gray-700">
          Running low on AI prompts? Hydrate your AI Assistant anytime—your Cups never expire.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { price: "$1", cups: "10" },
            { price: "$3", cups: "35" },
            { price: "$5", cups: "75" },
            { price: "$10", cups: "175" },
            { price: "$20", cups: "400" },
          ].map((pack) => (
            <div
              key={pack.price}
              className="bg-white rounded-lg shadow p-4 flex flex-col items-center"
            >
              <p className="text-lg font-semibold">{pack.price}</p>
              <p className="text-sm text-gray-600 mb-4">{pack.cups} Cups</p>
              <button className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition text-sm">
                Refill Your Cup
              </button>
            </div>
          ))}
        </div>
        <p className="text-sm text-gray-600 mt-4 italic">
          Pro tip: Drink a real cup of water each time you refill your AI Assistant.
        </p>
      </section>
    </main>
  );
}

