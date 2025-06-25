'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';
import './papyrus.css';



export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <main className="min-h-screen bg-green-900 text-white p-6 flex items-center justify-center">
        <p>Loading your dashboard...</p>
      </main>
    );
  }

  // dashboard code goes below this
  return (
    <main className="min-h-screen bg-green-900 text-gray-100 font-sans p-6 space-y-4">
      {/* Header */}
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

      {/* Food Journal */}
        <section className="w-full max-w-6xl mx-auto bg-amber-50 text-gray-800 p-6 rounded-xl shadow-md space-y-4">
            <h2 className="text-2xl font-bold text-green-800 papyrus">🥗 Food Journal</h2>
            <p>Track your meals, moods, and hydration with ease.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left column = form */}
                <div>
        <input
          type="text"
          name="food_name"
          value={journalEntry.food_name}
          onChange={async (e) => {
            const value = e.target.value;
            setJournalEntry((prev) => ({ ...prev, food_name: value }));

            if (value.length < 3) return;

            const res = await fetch('/api/food-lookup', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ food: value })
            });

            const data = await res.json();

            if (data?.error) {
              console.warn('Nutrition lookup failed:', data.error);
            } else {
              setJournalEntry((prev) => ({
                ...prev,
                protein_g: data.protein_g,
                carbs_g: data.carbs_g,
                fat_g: data.fat_g,
                calories: data.calories
              }));
            }
          }}
          placeholder="e.g. oatmeal"
          className="w-full p-2 border rounded"
        />

        {/* Show auto-filled results */}
        <div className="text-sm space-y-1">
          <p><strong>Protein:</strong> {journalEntry.protein_g}g</p>
          <p><strong>Carbs:</strong> {journalEntry.carbs_g}g</p>
          <p><strong>Fat:</strong> {journalEntry.fat_g}g</p>
          <p><strong>Calories:</strong> {journalEntry.calories}</p>
        </div>
              <div className="space-y-2">
        <select
            name="meal_type"
            value={journalEntry.meal_type}
            onChange={(e) => setJournalEntry(prev => ({ ...prev, meal_type: e.target.value }))}
            className="w-full p-2 border rounded"
        >
            <option value="">Select Meal Type</option>
            <option value="Breakfast">Breakfast</option>
            <option value="Lunch">Lunch</option>
            <option value="Dinner">Dinner</option>
            <option value="Snack">Snack</option>
        </select>

        <input
            type="number"
            name="servings"
            value={journalEntry.servings}
            onChange={(e) => setJournalEntry(prev => ({ ...prev, servings: e.target.value }))}
            className="w-full p-2 border rounded"
            placeholder="Servings"
        />

        <select
            name="mood"
            value={journalEntry.mood}
            onChange={(e) => setJournalEntry(prev => ({ ...prev, mood: e.target.value }))}
            className="w-full p-2 border rounded"
        >
            <option value="">Mood</option>
            <option value="Sad">Sad</option>
            <option value="Okay">Okay</option>
            <option value="Good">Good</option>
            <option value="Great">Great</option>
        </select>

        <textarea
            name="notes"
            value={journalEntry.notes}
            onChange={(e) => setJournalEntry(prev => ({ ...prev, notes: e.target.value }))}
            className="w-full p-2 border rounded"
            placeholder="Any notes..."
        />
        </div>
        <button
                onClick={async () => {
                    const { data: { user } } = await supabase.auth.getUser();
                    if (!user) {
                    alert('Please log in.');
                    return;
                    }

                    const { error } = await supabase.from('food_journal').insert({
                    ...journalEntry,
                    user_id: user.id,
                    servings: parseFloat(journalEntry.servings),
                    protein_g: parseFloat(journalEntry.protein_g),
                    carbs_g: parseFloat(journalEntry.carbs_g),
                    fat_g: parseFloat(journalEntry.fat_g),
                    calories: parseFloat(journalEntry.calories)
                    });

                    if (error) {
                    alert('Error saving entry: ' + error.message);
                    } else {
                    alert('Entry saved!');
                    setJournalEntry(prev => ({
                        ...prev,
                        food_name: '',
                        protein_g: '',
                        carbs_g: '',
                        fat_g: '',
                        calories: '',
                        servings: 1,
                        meal_type: '',
                        mood: '',
                        notes: ''
                    }));
                    }
                }}
                className="w-full bg-green-700 text-white p-2 rounded hover:bg-green-800"
                >
                Save Food Entry
            </button>
                </div>

                {/* Right column = table */}
                <div>
                <div className="overflow-auto max-h-[500px]">
                <table className="w-full text-sm border-collapse">
                    <thead>
                    <tr className="bg-green-100 text-left">
                        <th className="p-2">Date</th>
                        <th className="p-2">Food</th>
                        <th className="p-2">Protein</th>
                        <th className="p-2">Carbs</th>
                        <th className="p-2">Fat</th>
                        <th className="p-2">Calories</th>
                    </tr>
                    </thead>
                    <tbody>
                    {entries.map((entry) => (
                        <tr key={entry.id} className="border-t">
                        <td className="p-2">{entry.date}</td>
                        <td className="p-2">{entry.food_name}</td>
                        <td className="p-2">{entry.protein_g}</td>
                        <td className="p-2">{entry.carbs_g}</td>
                        <td className="p-2">{entry.fat_g}</td>
                        <td className="p-2">{entry.calories}</td>
                        </tr>
                    ))}
                    </tbody>
                </table>
                </div>

                </div>
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
