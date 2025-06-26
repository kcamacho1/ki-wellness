'use client'; // Enable client-side rendering for this Next.js page

// Import necessary hooks and tools
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js';


// Import modular components
import FoodJournalForm from '@/components/FoodJournalForm';
import FoodJournalTable from '@/components/FoodJournalTable';

import './papyrus.css'; // Custom styling (e.g. Papyrus font)

export default function DashboardPage() {
  const router = useRouter();

  // Track logged-in user
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // App loading state

  // Food journal entries pulled from database
  const [entries, setEntries] = useState<any[]>([]);

  // Nutrition AI feedback and status
  const [aiFeedback, setAiFeedback] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  /**
   * 1️⃣ Check authentication on page load
   */
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (!data?.user) {
        router.push('/login'); // Redirect if not logged in
      } else {
        setUser(data.user);
        setLoading(false); // Allow dashboard to load
      }
    });
  }, [router]);

  /**
   * 2️⃣ Fetch food journal entries from Supabase on load
   */
  useEffect(() => {
    const fetchEntries = async () => {
      const { data, error } = await supabase
        .from('food_journal')
        .select('*')
        .order('date', { ascending: false });

      if (data && !error) {
        setEntries(data); // Populate journal entries
      } else {
        console.error('Failed to fetch entries:', error);
      }
    };

    fetchEntries();
  }, []);

  /**
   * 3️⃣ Handle AI Nutrition Analysis
   */
  const handleAnalyze = async () => {
    setAnalyzing(true);

    const res = await fetch('/api/ai-nutrition-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries })
    });

    const data = await res.json();
    setAiFeedback(data.message || 'No feedback returned.');
    setAnalyzing(false);
  };

  /**
   * 4️⃣ Display a loading screen until the dashboard is ready
   */
  if (loading) {
    return (
      <main className="min-h-screen bg-green-900 text-white flex items-center justify-center">
        <p>Loading your dashboard...</p>
      </main>
    );
  }

  /**
   * 5️⃣ Render the main dashboard UI
   */
  return (
    <main className="min-h-screen bg-green-900 text-gray-100 p-6 space-y-4">

      {/* Header: App Name and Log Out */}
      <section className="max-w-6xl mx-auto bg-amber-50 p-6 rounded-xl shadow text-gray-800">
        <div className="text-right">
          <button
            onClick={async () => {
              await supabase.auth.signOut();
              router.push('/login');
            }}
            className="text-sm text-green-800 underline hover:text-red-600"
          >
            Log out
          </button>
        </div>
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-2">your dashboard</h1>
        <p className="text-gray-700">Journal your food, track your wellness, and analyze nutrition.</p>
      </section>

      {/* Food Journal Entry + Table + AI Analysis */}
      <section className="max-w-6xl mx-auto bg-amber-50 p-6 rounded-xl shadow text-gray-800 space-y-6">
        <h2 className="text-2xl font-bold text-green-800 papyrus mb-4">🥗 Food Journal</h2>

        {/* Two-column layout for form and table */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <FoodJournalForm user={user} onEntrySaved={() => location.reload()} />
          </div>
          <div className="overflow-auto max-h-[500px]">
            <FoodJournalTable entries={entries} />
          </div>
        </div>

        {/* AI Analysis in a full-width row below */}
        <div className="mt-6 flex flex-col items-center">
          <button
            onClick={handleAnalyze}
            className="bg-green-800 text-white px-4 py-2 rounded hover:bg-green-900"
          >
            {analyzing ? 'Analyzing...' : '🧠 AI review gaps and recommend'}
          </button>

          {aiFeedback && (
            <div className="mt-4 bg-green-100 text-green-900 p-4 rounded text-sm">
              <strong>AI Recommendation:</strong>
              <p>{aiFeedback}</p>
            </div>
          )}
        </div>
      </section>

      {/* SECTION: Meal Planner */}
      <section className="w-full max-w-6xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow-md space-y-2">
        <h2 className="text-2xl font-bold text-green-800 papyrus">📅 Meal Planner</h2>
        <p>Get personalized meal ideas based on your health goals.</p>
        {/* Add dropdowns or GPT-driven planner here */}
      </section>

      {/* SECTION: Exercise Playlist */}
      <section className="w-full max-w-6xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow-md space-y-2">
        <h2 className="text-2xl font-bold text-green-800 papyrus">💪 Exercise Playlist</h2>
        <p>Curated workouts and suggestions based on your fitness level.</p>
        {/* Add exercise suggestions, playlist builder, etc. */}
        {/* Example Card inside Exercise Playlist section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
        {[
            {
            title: "10-Minute Morning Workout",
            url: "https://www.youtube.com/watch?v=UBMk30rjy0o",
            thumbnail: "https://img.youtube.com/vi/UBMk30rjy0o/0.jpg",
            duration: "10:21"
            },
            {
            title: "15-Min Bodyweight HIIT",
            url: "https://www.youtube.com/watch?v=ml6cT4AZdqI",
            thumbnail: "https://img.youtube.com/vi/ml6cT4AZdqI/0.jpg",
            duration: "15:12"
            }
        ].map(({ title, url, thumbnail, duration }) => (
            <a
            key={title}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="block bg-white rounded-xl overflow-hidden shadow-md hover:shadow-lg transition"
            >
            <img src={thumbnail} alt={title} className="w-full h-48 object-cover" />
            <div className="p-4 text-gray-800">
                <h3 className="text-lg font-bold">{title}</h3>
                <p className="text-sm text-green-700">Duration: {duration}</p>
            </div>
            </a>
        ))}
        </div>

      </section>

      {/* SECTION: Spiritual Playlist */}
      <section className="w-full max-w-6xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow-md space-y-2">
        <h2 className="text-2xl font-bold text-green-800 papyrus">🧘‍♀️ Spiritual Playlist</h2>
        <p>Mindful practices, meditations, and journaling prompts.</p>
        {/* Could embed YouTube/audio or AI-generated prompts */}
                {/* Example Card inside Spiritual Playlist section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
        {[
            {
            title: "10-Minute Meditation Workout",
            url: "https://www.youtube.com/watch?v=-9KLB2HI9BI",
            thumbnail: "https://img.youtube.com/vi/-9KLB2HI9BI/0.jpg",
            duration: "10:54"
            },
            {
            title: "Breathwork for Stress Relief",
            url: "https://www.youtube.com/watch?v=DbDoBzGY3vo",
            thumbnail: "https://img.youtube.com/vi/DbDoBzGY3vo/0.jpg",
            duration: "15:12"
            }
        ].map(({ title, url, thumbnail, duration }) => (
            <a
            key={title}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="block bg-white rounded-xl overflow-hidden shadow-md hover:shadow-lg transition"
            >
            <img src={thumbnail} alt={title} className="w-full h-48 object-cover" />
            <div className="p-4 text-gray-800">
                <h3 className="text-lg font-bold">{title}</h3>
                <p className="text-sm text-green-700">Duration: {duration}</p>
            </div>
            </a>
        ))}
        </div>
      </section>
     </main>
  );
}
