// app/one-on-one/page.tsx
import './papyrus.css';

export default function OneOnOnePage() {
  return (
    <main className="min-h-screen bg-green-900 text-gray-800 font-sans p-6">
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-start p-4 border-2 border-green-900 rounded-xl">

        {/* Session Info */}
<<<<<<< HEAD
        <div className="bg-amber-50 border border-green-200 rounded-lg p-6 text-left text-gray-700">
=======
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-left text-gray-700">
>>>>>>> 30688121eaa0cdf5693a64bf0980cd04666f9d12
          <h1 className="text-4xl font-bold text-green-900 papyrus mb-4">Book a One-on-One Session</h1>
          <p className="text-lg text-gray-600 mb-6">
            Receive personalized wellness support from Kristina Camacho,<br />
            certified Nutrition Coach and Personal Trainer.
          </p>
          <h2 className="text-2xl font-semibold mb-3 papyrus text-green-900">Included in Your Session:</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>🔸 1 Hour Private Coaching Session</li>
            <li>🥗 Customized Meal Plan for 1 Month</li>
            <li>💪 Personalized Exercise Plan for 1 Month</li>
            <li>🎯 Goal Setting and Lifestyle Strategy Guidance</li>
          </ul>
        </div>

        {/* Calendly Booking */}
<<<<<<< HEAD
        <div className="w-full h-[900px] bg-amber-50 shadow rounded overflow-hidden">
=======
        <div className="w-full h-[900px] bg-green-50 shadow rounded overflow-hidden">
>>>>>>> 30688121eaa0cdf5693a64bf0980cd04666f9d12
          <br></br>
          <h2 className="text-2xl font-bold text-center text-green-600 papyrus mb-4">Schedule and Pay Securely</h2>
          <p className="text-center text-gray-600 mb-6">
            Sessions are $25 and paid directly through the embedded calendar below.
          </p>
          <iframe
            src="https://calendly.com/kiwellness/one-on-one"
            width="100%"
            height="100%"
            frameBorder="0"
            className="border-none w-full h-full"
            allowFullScreen
          ></iframe>
        </div>
      </section>
    </main>
  );
}
