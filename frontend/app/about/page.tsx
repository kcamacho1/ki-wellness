"use client";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6 space-y-8">
      {/* Section 1: What is Ki Wellness */}
      <section className="max-w-5xl mx-auto bg-white p-6 rounded-lg shadow space-y-4">
        <h1 className="text-4xl font-bold text-green-800 text-center papyrus">
          🌿 What is Ki Wellness?
        </h1>
        <p className="text-lg leading-relaxed text-center">
          Ki Wellness is an affordable, AI-powered platform that helps you nurture mind, body, and spirit. 
          With your personalized dashboard, it’s easy to start your wellness goals your way—
          and connect with a human coach anytime you need extra support.
        </p>
      </section>

      {/* Section 2: Core Features */}
      <section className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Features */}
        <div className="bg-white p-6 rounded-lg shadow space-y-4">
          <h2 className="text-2xl font-semibold text-green-800 papyrus">
            ✨ Core Features
          </h2>
          <ul className="space-y-2 text-lg">
            <li>🥗 Personal food journal & nutrition tracking</li>
            <li>📈 AI recommendations and insights</li>
            <li>🎵 Save & share playlists for exercise and mindfulness</li>
            <li>👥 Share meal plans and recipe cards</li>
            <li>⤵️ Download your logs to share with your care team</li>
            <li>🔔 Helpful reminders to keep you on track</li>
          </ul>
        </div>

        {/* Benefits */}
        <div className="bg-white p-6 rounded-lg shadow space-y-4">
          <h2 className="text-2xl font-semibold text-green-800 papyrus">
            💖 Benefits for You
          </h2>
          <ul className="space-y-2 text-lg">
            <li>💡 Clarity and confidence in your wellness journey</li>
            <li>⏳ All your plans in one place</li>
            <li>🌱 Accessible tools for every budget</li>
            <li>🤝 Support from caring human coaches</li>
            <li>🌿 A holistic approach to lasting well-being</li>
          </ul>
        </div>
      </section>

      {/* Section 3: Mission & Vision */}
      <section className="max-w-5xl mx-auto bg-white p-6 rounded-lg shadow space-y-4">
        <h2 className="text-2xl font-bold text-green-800 text-center papyrus">
          🌟 Our Mission & Vision
        </h2>
        <p className="text-lg leading-relaxed text-center">
          Ki Wellness is more than an app—it’s a movement to build healthier, happier communities.
        </p>
        <ul className="list-disc list-inside text-lg space-y-2 mt-4">
          <li>🌍 Provide free or affordable access to everyone</li>
          <li>💸 Fairly compensate users who share health data for research</li>
          <li>🏡 Open a retreat center for rest and learning</li>
          <li>🤝 Partner with insurers to sponsor memberships</li>
          <li>👐 Support practitioners who volunteer care to those in need</li>
        </ul>
      </section>

      {/* Section 4: Join Us */}
      <section className="max-w-5xl mx-auto bg-white p-6 rounded-lg shadow text-center space-y-4">
        <h2 className="text-2xl font-bold text-green-800 papyrus">
          🌿 Join the Movement
        </h2>
        <p className="text-lg leading-relaxed">
          I built Ki Wellness for you, for me, and for a healthier tomorrow.
          Together, we can create positive, generational change—one healthy habit at a time.
        </p>
        <div className="flex flex-col md:flex-row gap-4 justify-center mt-4">
          <a
            href="https://donate.stripe.com/7sYdR95ld0R9byt8VU3Je02"
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
          >
            💖 Donate to Support
          </a>
          <a
            href="https://medium.com/@ki_wellness"
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
          >
            🌱 Follow Us on Medium
          </a>
        </div>
      </section>
    </main>
  );
}
