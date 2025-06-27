"use client";
import Image from "next/image";

export default function ResourcesPage() {
  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6 space-y-8">

      {/* Header */}
      <section className="max-w-6xl mx-auto text-center bg-white p-6 rounded-lg shadow">
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-2">
          🌿 Free Resources
        </h1>
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
            img: "/documents/meditationguide.png",
            desc: "Foundational tips and guidance for starting meditation practice."
          },
        ].map(({ title, href, img, desc }) => (
          <div
            key={title}
            className="bg-white border border-green-200 rounded-lg shadow p-4 flex flex-col items-center text-center space-y-4 hover:shadow-md transition"
          >
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
              rel="noopener noreferrer"
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
            >
              Download PDF
            </a>
          </div>
        ))}
      </section>

      {/* Medium Section */}
      <section className="max-w-6xl mx-auto bg-white p-6 rounded-lg shadow text-center">
        <h2 className="text-2xl font-bold text-green-800 papyrus mb-2">
          📝 More Articles & FAQs
        </h2>
        <p className="text-lg text-gray-700 mb-4">
          For deeper dives, practical tips, and frequently asked questions, visit our Medium page.
        </p>
        <a
          href="https://medium.com/@ki_wellness"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-green-600 text-white font-semibold px-6 py-3 rounded hover:bg-green-700 transition"
        >
          Visit Blog on Medium
        </a>
      </section>

    </main>
  );
}
