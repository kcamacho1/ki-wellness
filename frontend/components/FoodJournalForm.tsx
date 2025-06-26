'use client';

import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';

export default function FoodJournalForm({ user, onEntrySaved }) {
  const [entry, setEntry] = useState({
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

  const fetchNutrition = async (food: string) => {
    const res = await fetch('/api/food-lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ food })
    });
    const data = await res.json();
    if (!data.error) {
      setEntry((prev) => ({
        ...prev,
        protein_g: data.protein_g,
        carbs_g: data.carbs_g,
        fat_g: data.fat_g,
        calories: data.calories
      }));
    }
  };

  const handleSave = async () => {
    if (!user) return alert('Please log in.');

    const { error } = await supabase.from('food_journal').insert({
      ...entry,
      user_id: user.id,
      servings: parseFloat(entry.servings),
      protein_g: parseFloat(entry.protein_g),
      carbs_g: parseFloat(entry.carbs_g),
      fat_g: parseFloat(entry.fat_g),
      calories: parseFloat(entry.calories)
    });

    if (error) alert('Error saving entry: ' + error.message);
    else {
      onEntrySaved();
      setEntry({
        ...entry,
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
    }
  };

  return (
    <div className="space-y-2">
      <input
        type="text"
        name="food_name"
        value={entry.food_name}
        onChange={(e) => {
          const value = e.target.value;
          setEntry((prev) => ({ ...prev, food_name: value }));
          if (value.length >= 3) fetchNutrition(value);
        }}
        placeholder="e.g. oatmeal"
        className="w-full p-2 border bg-white rounded"
      />
      <select name="meal_type" value={entry.meal_type} onChange={(e) => setEntry({ ...entry, meal_type: e.target.value })} className="w-full p-2 border bg-white rounded">
        <option value="">Meal Type</option>
        <option value="Breakfast">Breakfast</option>
        <option value="Lunch">Lunch</option>
        <option value="Dinner">Dinner</option>
        <option value="Snack">Snack</option>
      </select>
      <input type="number" name="servings" value={entry.servings} onChange={(e) => setEntry({ ...entry, servings: e.target.value })} className="w-full p-2 border rounded bg-white" placeholder="Servings" />
      <select name="serving_unit" value={entry.serving_unit} onChange={(e) => setEntry({ ...entry, serving_unit: e.target.value })} className="w-full p-2 border bg-white rounded">
        <option value="">Unit</option>
        <option value="g">grams (g)</option>
        <option value="oz">ounces (oz)</option>
        <option value="cup">cup</option>
        <option value="tbsp">tablespoon</option>
        <option value="tsp">teaspoon</option>
        <option value="slice">slice</option>
        <option value="piece">piece</option>
      </select>
      <select name="mood" value={entry.mood} onChange={(e) => setEntry({ ...entry, mood: e.target.value })} className="w-full p-2 border bg-white rounded">
        <option value="">Mood</option>
        <option value="Sad">Sad</option>
        <option value="Okay">Okay</option>
        <option value="Good">Good</option>
        <option value="Great">Great</option>
      </select>
      <textarea name="notes" value={entry.notes} onChange={(e) => setEntry({ ...entry, notes: e.target.value })} className="w-full p-2 border bg-white rounded" placeholder="Notes..." />
      <button onClick={handleSave} className=" bg-green-700 text-white p-2 rounded hover:bg-green-800">Save Entry</button>
    </div>
  );
}
