'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';
import './papyrus.css';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiFeedback, setAiFeedback] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  const [journalEntry, setJournalEntry] = useState({
    date: new Date().toISOString().slice(0, 10),
    meal_type: '',
    food_name: '',
    servings: 1,
    serving_unit: '',
    protein_g: '',
    carbs_g: '',
    fat_g: '',
    calories: '',
    mood: '',
    notes: ''
  });

  const [entries, setEntries] = useState<any[]>([]);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (!data?.user) {
        router.push('/login');
      } else {
        setUser(data.user);
        setLoading(false);
      }
    });
  }, [router]);

  useEffect(() => {
    const fetchEntries = async () => {
      const { data, error } = await supabase
        .from('food_journal')
        .select('*')
        .order('date', { ascending: false });

      if (!error && data) {
        setEntries(data);
      } else {
        console.error('Failed to fetch entries', error);
      }
    };

    fetchEntries();
  }, []);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    const response = await fetch('/api/ai-nutrition-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries })
    });
    const data = await response.json();
    setAiFeedback(data.message || 'No feedback returned.');
    setAnalyzing(false);
  };

  const handleSaveEntry = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      alert('Please log in.');
      return;
    }

    const { error } = await supabase.from('food_journal').insert({
      ...journalEntry,
      user_id: user.id,
      servings: parseFloat(journalEntry.servings),
      serving_unit: journalEntry.serving_unit,
      protein_g: parseFloat(journalEntry.protein_g),
      carbs_g: parseFloat(journalEntry.carbs_g),
      fat_g: parseFloat(journalEntry.fat_g),
      calories: parseFloat(journalEntry.calories)
    });

    if (error) {
      alert('Error saving entry: ' + error.message);
    } else {
      setJournalEntry(prev => ({
        ...prev,
        food_name: '',
        servings: 1,
        serving_unit: '',
        protein_g: '',
        carbs_g: '',
        fat_g: '',
        calories: '',
        meal_type: '',
        mood: '',
        notes: ''
      }));
      const { data, error } = await supabase
        .from('food_journal')
        .select('*')
        .order('date', { ascending: false });

      if (!error && data) setEntries(data);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-green-900 text-white p-6 flex items-center justify-center">
        <p>Loading your dashboard...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-green-900 text-gray-100 font-sans p-6 space-y-4">
      <section className="max-w-6xl mx-auto text-center border-2 border-green-900 rounded-xl p-6 bg-amber-50 text-gray-800">
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
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-4">your dashboard</h1>
        <p className="text-lg text-gray-700">Journal your food, save meals, favorite exercises and spiritual videos.</p>
        <p>Set reminders and stay balanced 🧘</p>
      </section>

      <section className="w-full max-w-6xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow-md space-y-4">
        <h2 className="text-2xl font-bold text-green-800 papyrus">🥗 Food Journal</h2>
        <p>Track your meals, moods, and hydration with ease.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <select
            name="serving_unit"
            value={journalEntry.serving_unit || ''}
            onChange={(e) => setJournalEntry((prev) => ({ ...prev, serving_unit: e.target.value }))}
            className="w-full p-2 border rounded bg-white"
          >
            <option value="">Select Unit</option>
            <option value="g">grams (g)</option>
            <option value="oz">ounces (oz)</option>
            <option value="cup">cup</option>
            <option value="tbsp">tablespoon</option>
            <option value="tsp">teaspoon</option>
            <option value="slice">slice</option>
            <option value="piece">piece</option>
          </select>
        </div>

        <div className="overflow-auto max-h-[500px]">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-green-100 text-left">
                <th className="p-2">Date</th>
                <th className="p-2">Food</th>
                <th className="p-2">Servings</th>
                <th className="p-2">Unit</th>
                <th className="p-2">Protein</th>
                <th className="p-2">Carbs</th>
                <th className="p-2">Fat</th>
                <th className="p-2">Calories</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry: any) => (
                <tr key={entry.id} className="border-t">
                  <td className="p-2">{entry.date}</td>
                  <td className="p-2">{entry.food_name}</td>
                  <td className="p-2">{entry.servings}</td>
                  <td className="p-2">{entry.serving_unit}</td>
                  <td className="p-2">{entry.protein_g}</td>
                  <td className="p-2">{entry.carbs_g}</td>
                  <td className="p-2">{entry.fat_g}</td>
                  <td className="p-2">{entry.calories}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4">
          <button
            onClick={handleAnalyze}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            {analyzing ? 'Analyzing...' : '🧠 Analyze My Nutrition'}
          </button>
        </div>
        {aiFeedback && (
          <div className="mt-3 text-green-900 bg-green-100 p-3 rounded">
            <strong>AI Recommendation:</strong>
            <p>{aiFeedback}</p>
          </div>
        )}
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
