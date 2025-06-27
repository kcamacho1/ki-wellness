import Image from 'next/image';
import './papyrus.css';

export default function ResourcesPage() {
  return (
    <main className="min-h-screen bg-green-900 text-gray-200 font-sans p-6 space-y-8">

      {/* Header */}
      <section className="max-w-6xl mx-auto text-center border-2 border-green-900 rounded-xl p-6 bg-amber-50 text-gray-800">
        <h1 className="text-3xl font-bold text-green-800 papyrus mb-4">Free Resources</h1>
        <p className="text-lg text-gray-700">
          Download guides and explore practical health & fitness tools created to empower you.
        </p>
      </section>

      {/* Pinned Resources as Cards */}
      <section className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            title: "7-Day Meal Tracker",
            href: "/documents/7daymealtracker.pdf",
            img: "/documents/7daymealtracker.png",
            desc: "A printable meal and mood tracker to support healthy routines."
          },
          {
            title: "Home Workout Plan",
            href: "/documents/homeworkoutplan.pdf",
            img: "/documents/homeworkoutplan.png",
            desc: "A no-equipment plan to keep you active at home or on the go."
          },
          {
            title: "Meditation for Beginners",
            href: "/documents/meditationguide.pdf",
            img: "/documents/meditationguide.png", // Add preview image if desired
            desc: "Foundational tips and guidance for starting meditation practice."
          },
        ].map(({ title, href, img, desc }) => (
          <div key={title} className="bg-amber-50 border border-green-800 rounded-xl shadow-md p-4 flex flex-col items-center text-center space-y-4 hover:shadow-lg transition">
            <Image
              src={img}
              alt={title}
              width={200}
              height={120}
              className="rounded"
            />
            <h3 className="text-xl font-bold text-green-800 papyrus">{title}</h3>
            <p className="text-sm text-gray-700">{desc}</p>
            <a
              href={href}
              target="_blank"
              className="bg-green-700 text-white px-4 py-2 rounded-full hover:bg-green-800 transition"
            >
              Download PDF
            </a>
          </div>
        ))}
      </section>

      {/* Medium Section */}
      <section className="max-w-6xl mx-auto border-2 border-green-900 rounded-xl p-6 text-center bg-amber-50 text-gray-800">
        <h2 className="text-3xl font-bold text-green-800 papyrus mb-4">More Articles & FAQs</h2>
        <p className="text-lg text-gray-700 mb-4">
          For deeper dives, practical tips, and frequently asked questions, visit our Medium page.
        </p>
        <a
          href="https://medium.com/@ki_wellness"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-green-700 text-white font-semibold px-6 py-3 rounded-full hover:bg-green-800 transition"
        >
          Visit Blog on Medium
        </a>
      </section>

    </main>
  );
}
