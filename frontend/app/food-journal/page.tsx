"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";

type Entry = {
  id: string;
  date: string;
  date_logged: string;
  meal_type: string;
  meal: string;
  serving_quantity: number;
  serving_size: string;
  protein: number;
  fat: number;
  carbs: number;
  calories: number;
  mood: string;
  notes: string;
};

export default function FoodJournalPage() {
  const [user, setUser] = useState<any>(null);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [mealType, setMealType] = useState("Breakfast");
  const [meal, setMeal] = useState("");
  const [servingQuantity, setServingQuantity] = useState("");
  const [servingSize, setServingSize] = useState("");
  const [protein, setProtein] = useState("");
  const [fat, setFat] = useState("");
  const [carbs, setCarbs] = useState("");
  const [calories, setCalories] = useState("");
  const [mood, setMood] = useState("");
  const [notes, setNotes] = useState("");
  const router = useRouter();
  const [showForm, setShowForm] = useState(false);


  // Load user & entries
  useEffect(() => {
    const init = async () => {
      const { data: sessionData } = await supabase.auth.getSession();
      const currentUser = sessionData.session?.user ?? null;
      setUser(currentUser);

      if (currentUser) {
        const { data, error } = await supabase
          .from("food_journal")
          .select("*")
          .eq("user_id", currentUser.id)
          .order("date_logged", { ascending: false });
        if (error) console.error(error);
        else setEntries(data || []);
      } else {
        const saved = localStorage.getItem("foodJournal");
        if (saved) setEntries(JSON.parse(saved));
      }
    };
    init();
  }, []);

  // Save to localStorage when not logged in
  useEffect(() => {
    if (!user) {
      localStorage.setItem("foodJournal", JSON.stringify(entries));
    }
  }, [entries, user]);

  async function handleAdd() {
    if (!meal || !calories) {
      alert("Please fill out at least Meal and Calories.");
      return;
    }

    const newEntry: Entry = {
      id: Date.now().toString(),
      date: new Date().toLocaleDateString(),
      date_logged: new Date().toISOString(),
      meal_type: mealType,
      meal,
      serving_quantity: Number(servingQuantity),
      serving_size: servingSize,
      protein: Number(protein),
      fat: Number(fat),
      carbs: Number(carbs),
      calories: Number(calories),
      mood,
      notes,
    };

    if (user) {
      const { error } = await supabase.from("food_journal").insert([
        {
          user_id: user.id,
          date: newEntry.date,
          date_logged: newEntry.date_logged,
          meal_type: newEntry.meal_type,
          meal: newEntry.meal,
          serving_quantity: newEntry.serving_quantity,
          serving_size: newEntry.serving_size,
          protein: newEntry.protein,
          fat: newEntry.fat,
          carbs: newEntry.carbs,
          calories: newEntry.calories,
          mood: newEntry.mood,
          notes: newEntry.notes,
        },
      ]);
      if (error) {
        console.error("Supabase insert error:", JSON.stringify(error, null, 2));
        alert("Error saving entry.");
      } else {
        const { data } = await supabase
          .from("food_journal")
          .select("*")
          .eq("user_id", user.id)
          .order("date_logged", { ascending: false });
        setEntries(data || []);
      }
    } else {
      if (entries.length >= 3) {
        alert("Create a free account to log more than 3 entries.");
        router.push("/login");
        return;
      }
      setEntries([newEntry, ...entries]);
    }

    setMeal("");
    setServingQuantity("");
    setServingSize("");
    setProtein("");
    setFat("");
    setCarbs("");
    setCalories("");
    setMood("");
    setNotes("");
    setMealType("Breakfast");
  }

  async function handleDelete(id: string) {
    if (user) {
      const { error } = await supabase
        .from("food_journal")
        .delete()
        .eq("id", id)
        .eq("user_id", user.id);
      if (error) {
        console.error(error);
        alert("Error deleting entry.");
      } else {
        setEntries(entries.filter((e) => e.id !== id));
      }
    } else {
      setEntries(entries.filter((e) => e.id !== id));
    }
  }

  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6 space-y-8">
      {/* Header */}
      <section className="max-w-6xl mx-auto bg-white p-6 rounded-lg shadow text-center">
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-2">
          📔 Food Journal
        </h1>
        <p className="text-lg text-gray-700">
          {user
            ? `Logged in as ${user.email}`
            : "Log meals and track progress. (Max 3 entries without an account)"}
        </p>
      </section>

        <div className="max-w-2xl mx-auto mb-4 text-center">
        <button
            onClick={() => setShowForm(!showForm)}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
        >
            {showForm ? "Hide Entry Form" : "Add New Entry"}
        </button>
        </div>
            {showForm && (
            <section className="max-w-2xl mx-auto bg-white p-4 rounded-lg shadow space-y-4">
                 {/* Add Entry */}
                <div className="w-full">
                <label className="block mb-1 text-sm font-medium text-gray-700">Meal Type</label>
                <select
                    value={mealType}
                    onChange={(e) => setMealType(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                >
                    <option value="Breakfast">Breakfast</option>
                    <option value="Lunch">Lunch</option>
                    <option value="Dinner">Dinner</option>
                    <option value="Snack">Snack</option>
                </select>
                </div>
                <input
                type="text"
                placeholder="Meal description"
                value={meal}
                onChange={(e) => setMeal(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <div className="grid grid-cols-2 gap-2">
                <input
                    type="number"
                    placeholder="Servings"
                    value={servingQuantity}
                    onChange={(e) => setServingQuantity(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2"
                />
                <input
                    type="text"
                    placeholder="Serving size (e.g., cup)"
                    value={servingSize}
                    onChange={(e) => setServingSize(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2"
                />
                </div>
                <div className="grid grid-cols-3 gap-2">
                <input
                    type="number"
                    placeholder="Protein (g)"
                    value={protein}
                    onChange={(e) => setProtein(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2"
                />
                <input
                    type="number"
                    placeholder="Fat (g)"
                    value={fat}
                    onChange={(e) => setFat(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2"
                />
                <input
                    type="number"
                    placeholder="Carbs (g)"
                    value={carbs}
                    onChange={(e) => setCarbs(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2"
                />
                </div>
                <input
                type="number"
                placeholder="Calories"
                value={calories}
                onChange={(e) => setCalories(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <input
                type="text"
                placeholder="Mood"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <textarea
                placeholder="Notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                />
                <button
                onClick={handleAdd}
                className="w-full bg-green-600 text-white font-semibold py-2 rounded hover:bg-green-700 transition"
                >
                Add Entry
                </button>
            </section>
            )}

     

      {/* Entries Table */}
      <section className="max-w-6xl mx-auto bg-white p-4 rounded-lg shadow overflow-x-auto">
        {entries.length === 0 ? (
          <p className="text-center text-gray-600">No entries yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left">
                <th className="py-2">Date</th>
                <th>Meal Type</th>
                <th>Meal</th>
                <th>Calories</th>
                <th>Mood</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-t border-gray-200">
                  <td className="py-2">{e.date}</td>
                  <td>{e.meal_type}</td>
                  <td>{e.meal}</td>
                  <td>{e.calories}</td>
                  <td>{e.mood}</td>
                  <td>
                    <button
                      onClick={() => handleDelete(e.id)}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
