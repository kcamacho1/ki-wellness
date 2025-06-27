// app/about/page.tsx

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-green-900 text-gray-200 font-sans p-6 space-y-5">
      
      {/* Section 1: What is Ki Wellness */}
      <section className="max-w-5xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow space-y-4">
        <p></p>
        <h1 className="text-4xl font-semibold text-green-800 text-center mb-4 papyrus">
           what are we
        </h1>
        <p className="text-lg leading-relaxed text-center">
          Ki Wellness is an affordable, AI-powered wellness platform to support your health journey in nourishing your mind, body, and spirit.
          With your personalized dashboard it is easy to jump into your health goals in a way that works for you. Visit with a human coach only when needed or for a more personalized approach.
        </p>
      </section>

      {/* Section 2: Features & Benefits */}
      <section className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 bg-amber-50 text-gray-800 p-6 rounded-xl shadow">
        <div className="space-y-4">
          <p></p>
          <h2 className="text-2xl font-semibold text-green-800 papyrus">Core Features</h2>
          <ul className="list-none list-inside text-lg space-y-2">
            <li>🥗 Personal <i className="papyrus">Food journal</i></li>
            <li>📈 <i className="papyrus">AI insights</i> and personalized suggestions</li>
            <li>🎵 Save & share your playlists</li>
            <li>👥 Share meal plans & recipes</li>
            <li>⤵️ Download your Food Journal for Doctor visits</li>
            <li>🔔 <b className="font-semibold papyrus">Push notifications to stay on track!!</b></li>
          </ul>
        </div>
        <div className="space-y-4">
          <p></p>
          <h2 className="text-2xl font-semibold text-green-800 papyrus">Benefits for You</h2>
          <ul className="list-none list-inside text-lg space-y-2">
            <li>💡 <b>Easy:</b> Clarity and confidence in your wellness journey</li>
            <li>⏳ <b>Save time:</b> all plans in one place</li>
            <li>🌱 <b>Accessible:</b> Tools no matter your income</li>
            <li>🤝 <b>Human:</b> Support from caring practitioners</li>
            <li>💖 <i className="papyrus">A holistic approach to long-term well-being</i></li>
          </ul>
        </div>
      </section>

      {/* Section 3: Pricing */}
      <section className="max-w-5xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow space-y-4">
        <h2 className="text-2xl font-bold text-green-800 text-center papyrus">Pricing & Accessibility</h2>
        <p className="text-lg text-center">
          We believe health should be affordable for everyone.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div className="bg-white rounded-lg p-4 shadow text-center">
            <h3 className="text-xl font-semibold text-green-700 mb-2">Basic Tier</h3>
            <p className="text-lg">$2/month</p>
            <p className="text-gray-600 mt-2">Essential tools to track your health and progress.</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow text-center">
            <h3 className="text-xl font-semibold text-green-700 mb-2">Premium Tier</h3>
            <p className="text-lg">$5/month</p>
            <p className="text-gray-600 mt-2">Includes AI analysis, GPT recommendations, and personalized wellness insights.</p>
          </div>
        </div>
      </section>

      {/* Section 4: Mission & Vision */}
      <section className="max-w-5xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow space-y-4">
        <h2 className="text-2xl font-bold text-green-800 text-center papyrus">Our Mission & Vision</h2>
        <p className="text-lg leading-relaxed">
          Ki Wellness is more than an app—it's a movement to empower healthier, happier communities.
          <br /><br />
          Our goals include:
        </p>
        <ul className="list-disc list-inside text-lg space-y-2">
          <li>🌍 Providing free or affordable access for everyone</li>
          <li>💸 Fairly compensating users who choose to share health data for research</li>
          <li>🏡 Opening a retreat center for rest, education, and holistic healing</li>
          <li>🤝 Partnering with insurers and healthcare providers to sponsor memberships</li>
          <li>👐 Supporting vetted practitioners who give back through volunteer care</li>
        </ul>
      </section>

      {/* Section 5: Closing Message */}
      <section className="max-w-5xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow text-center space-y-4">
        <h2 className="text-2xl font-bold text-green-800 papyrus">Join Us</h2>
        <p className="text-lg leading-relaxed">
          I built Ki Wellness for you, for me, and for a better tomorrow.
        </p>

        <p className="text-lg leading-relaxed">
          Together, we can create positive, generational change—one healthy habit at a time.
        </p>
        <p>
          <a href="https://donate.stripe.com/aFa14n5ldbvN7idege3Je00">Donate to support this mission </a> or 
          <a href="#"> Follow us on socials</a>
        </p>

      </section>

    </main>
  );
}
