// Updated to fetch nutrition only on submission
'use client';

import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js';

interface FoodJournalFormProps {
  user: User | null;
  onEntrySaved: () => void;
}

export default function FoodJournalForm({ user, onEntrySaved }: FoodJournalFormProps) {
  const [entry, setEntry] = useState({
    date: new Date().toISOString().slice(0, 10),
    meal_type: '',
    food_name: '',
    servings: '1',
    serving_unit: '',
    protein_g: '',
    carbs_g: '',
    fat_g: '',
    calories: '',
    mood: '',
    notes: ''
  });

  const fetchNutrition = async (food: string) => {
    try {
      const res = await fetch('https://ki-wellness-75gt.onrender.com/api/ai-nutrition-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ food })
      });
      const data = await res.json();

      if (!data.error) {
        setEntry((prev) => ({
          ...prev,
          protein_g: data.protein_g != null ? String(data.protein_g) : '',
          carbs_g: data.carbs_g != null ? String(data.carbs_g) : '',
          fat_g: data.fat_g != null ? String(data.fat_g) : '',
          calories: data.calories != null ? String(data.calories) : ''
        }));
        return true;
      } else {
        console.error('Nutrition lookup error:', data.error);
        return false;
      }
    } catch (error) {
      console.error('Failed to fetch nutrition data:', error);
      return false;
    }
  };

  const handleSave = async () => {
    if (!user) {
      console.error('User not logged in. Cannot save entry.');
      return;
    }

    const nutritionFetched = await fetchNutrition(entry.food_name);
    if (!nutritionFetched) {
      console.error("Couldn't fetch nutrition before saving.");
      return;
    }

    try {
      const { error } = await supabase.from('food_journal').insert({
        ...entry,
        user_id: user.id,
        servings: parseFloat(entry.servings) || 0,
        protein_g: parseFloat(entry.protein_g) || 0,
        carbs_g: parseFloat(entry.carbs_g) || 0,
        fat_g: parseFloat(entry.fat_g) || 0,
        calories: parseFloat(entry.calories) || 0
      });

      if (error) {
        console.error('Error saving entry:', error.message);
      } else {
        onEntrySaved();
        setEntry((prev) => ({
          ...prev,
          food_name: '',
          servings: '1',
          serving_unit: '',
          protein_g: '',
          carbs_g: '',
          fat_g: '',
          calories: '',
          mood: '',
          notes: ''
        }));
      }
    } catch (error) {
      console.error('Unexpected error during save:', error);
    }
  };

  return (
    <div className="max-w-md mx-auto p-3 bg-white rounded-lg shadow space-y-4 text-sm">
      <div>
        <label htmlFor="csvUpload" className="block font-semibold text-green-700 mb-1">Upload CSV</label>
        <input type="file" id="csvUpload" accept=".csv" className="block w-full text-sm" />
      </div>

      <h3 className="text-lg font-bold text-green-800">Log Your Meal</h3>

      <input type="date" value={entry.date} onChange={(e) => setEntry({ ...entry, date: e.target.value })} className="w-full p-2 border rounded" />

      <input type="text" placeholder="Food Name" value={entry.food_name} onChange={(e) => setEntry({ ...entry, food_name: e.target.value })} className="w-full p-2 border rounded" />

      <select value={entry.meal_type} onChange={(e) => setEntry({ ...entry, meal_type: e.target.value })} className="w-full p-2 border rounded">
        <option value="">Meal Type</option>
        <option value="Breakfast">Breakfast</option>
        <option value="Lunch">Lunch</option>
        <option value="Dinner">Dinner</option>
        <option value="Snack">Snack</option>
      </select>

      <div className="grid grid-cols-2 gap-2">
        <input type="number" value={entry.servings} onChange={(e) => setEntry({ ...entry, servings: e.target.value })} placeholder="Servings" className="w-full p-2 border rounded" step="0.1" />
        <select value={entry.serving_unit} onChange={(e) => setEntry({ ...entry, serving_unit: e.target.value })} className="w-full p-2 border rounded">
          <option value="">Unit</option>
          <option value="g">grams</option>
          <option value="oz">ounces</option>
          <option value="cup">cup</option>
          <option value="tbsp">tbsp</option>
          <option value="tsp">tsp</option>
          <option value="slice">slice</option>
          <option value="piece">piece</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <input type="text" value={entry.protein_g} readOnly placeholder="Protein (g)" className="w-full p-2 border rounded bg-gray-100" />
        <input type="text" value={entry.carbs_g} readOnly placeholder="Carbs (g)" className="w-full p-2 border rounded bg-gray-100" />
        <input type="text" value={entry.fat_g} readOnly placeholder="Fat (g)" className="w-full p-2 border rounded bg-gray-100" />
        <input type="text" value={entry.calories} readOnly placeholder="Calories" className="w-full p-2 border rounded bg-gray-100" />
      </div>

      <select value={entry.mood} onChange={(e) => setEntry({ ...entry, mood: e.target.value })} className="w-full p-2 border rounded">
        <option value="">Mood</option>
        <option value="Sad">Sad</option>
        <option value="Okay">Okay</option>
        <option value="Good">Good</option>
        <option value="Great">Great</option>
      </select>

      <textarea value={entry.notes} onChange={(e) => setEntry({ ...entry, notes: e.target.value })} placeholder="Notes..." className="w-full p-2 border rounded resize-y min-h-[60px]" />

      <button onClick={handleSave} className="w-full bg-green-700 hover:bg-green-800 text-white p-2 rounded">
        Save Entry
      </button>
    </div>
  );
}
