'use client';
import Link from 'next/link';

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-green-900 text-white p-6 font-sans">
      <section className="max-w-5xl mx-auto text-center space-y-4">
        <h1 className="text-4xl font-bold text-amber-300 papyrus">🌱 Ki Wellness Pricing</h1>
        <p className="text-lg text-gray-200">
          Choose a plan that fits your journey. Start free, grow empowered.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          {/* Essentials Plan */}
          <div className="bg-amber-50 text-gray-900 p-6 rounded-xl shadow-lg space-y-4">
            <h2 className="text-2xl font-bold text-green-800">Essentials</h2>
            <p className="text-sm text-gray-600">7-day free trial · then $2/month</p>
            <div className="space-y-1 text-left text-sm mt-4">
              <p>✅ Food journal with macro tracking</p>
              <p>✅ Save & delete meals, workouts, and spiritual content</p>
              <p>✅ 1 AI-powered meal suggestion per month</p>
              <p>✅ Dashboard access with YouTube embeds</p>
            </div>
            <button className="block w-full bg-green-700 hover:bg-green-800 text-white py-2 rounded mt-4">
              Start 7-Day Free Trial
            </button>
          </div>

          {/* AI Wellness Pro */}
          <div className="bg-white text-gray-900 p-6 rounded-xl shadow-lg space-y-4 border-4 border-green-700">
            <h2 className="text-2xl font-bold text-green-800">AI Wellness Pro</h2>
            <p className="text-sm text-gray-600">$5/month</p>
            <div className="space-y-1 text-left text-sm mt-4">
              <p>✅ All Essentials features</p>
              <p>✅ Unlimited AI nutrition analysis</p>
              <p>✅ AI meal + supplement suggestions</p>
              <p>✅ AI-powered fitness & spiritual coaching</p>
            </div>
            <button className="block w-full bg-green-700 hover:bg-green-800 text-white py-2 rounded mt-4">
              Go Pro
            </button>
          </div>

          {/* 1-on-1 Coaching */}
          <div className="bg-amber-100 text-gray-900 p-6 rounded-xl shadow-lg space-y-4">
            <h2 className="text-2xl font-bold text-green-800">1-on-1 Coaching</h2>
            <p className="text-sm text-gray-600">$100/hour</p>
            <div className="space-y-1 text-left text-sm mt-4">
              <p>✅ Personalized health consulting</p>
              <p>✅ Live Zoom sessions with Kristina</p>
              <p>✅ Customized healing, fitness, and spiritual plans</p>
              <p>✅ Limited slots available</p>
            </div>
            <Link
              href="/one-on-one"
              className="block w-full bg-green-700 hover:bg-green-800 text-white py-2 rounded mt-4 text-center"
            >
              Book a Session
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
