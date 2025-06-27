// app/about/page.tsx
import Image from 'next/image';
import './papyrus.css';

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-green-900 text-gray-200 font-sans p-6 space-y-4 rounded-xl">

      {/* Top Section: Photo and Credentials */}
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-start p-4 border-2 border-green-900 rounded-xl bg-amber-50 text-gray-800">
        <div className="text-center">
          <Image
            src="/profileBooks.png"
            alt="Kristina Camacho"
            width={300}
            height={300}
            className="rounded-xl mx-auto shadow-md mb-4"
          />
          <h3 className="text-xl font-semibold text-green-900">Kristina Camacho</h3>
          <p className="text-gray-600">Founder of Ki Wellness</p>
        </div>

        <div className="text-left">
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-green-900 papyrus mb-4">Credentials</h2>
            <ul className="list-disc list-inside space-y-3 text-lg text-gray-700">
              <li>📁 Project Manager</li>
              <li>🥗 Certified Nutritionist</li>
              <li>💪 Certified Personal Trainer</li>
              <li>⛑️ CPR & First Aid Certified</li>
              <li>💻 Full Stack Developer</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Heartfelt Message and Certificates Side by Side */}
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 p-4 border-2 border-green-900 rounded-xl bg-amber-50 text-gray-800">
        <div className="text-left">
            <br></br>
          <h2 className="text-3xl font-bold text-green-800 papyrus mb-6 text-center md:text-left">Why I Built Ki Wellness</h2>
          <p className="text-lg text-gray-700 leading-relaxed">
            I made this app for you. Yes you.
            <br /><br />
            Let that sink in. I made this app for me and for you. An app that provides basic health information at an affordable or free price to everyone is my goal.
            <br /><br />
            My belief is that if you are feeling healthier and better then you will be better able to meet stressful situations with confidence and more clearly support yourself and those you love. It is this change from within that exponentially trickles outward creating generational changes if we allow it.
            <br /><br />
            So join me in changing the world by changing ourselves for the better. For you. For me. For a better tomorrow.
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <br></br>
            <br></br>
            {/* Nutritionist Certification */}
                <Image
                src="/2025nutritionistCert.png"
                alt="Certified Nutritionist Certificate"
                width={800}
                height={600}
                className="rounded shadow-md w-full object-contain"
                />
          </div>
          <div>
            {/* Personal Training Certification */}
                <Image
                src="/2025PTcert.png"
                alt="Certified Personal Trainer Certificate"
                width={800}
                height={600}
                className="rounded shadow-md w-full object-contain"
                />
          </div>
        </div>
      </section>
    </main>
  );
}
