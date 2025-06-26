'use client';

import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js'; // Import User type for props

/**
 * Interface for the FoodJournalForm component's props.
 * @property {User | null} user - The Supabase user object, or null if not logged in.
 * @property {() => void} onEntrySaved - Callback function executed after an entry is successfully saved.
 */
interface FoodJournalFormProps {
  user: User | null;
  onEntrySaved: () => void;
}

/**
 * FoodJournalForm Component
 * This component provides a form for users to input food entries,
 * including integration with a nutrition lookup API and saving to Supabase.
 */
export default function FoodJournalForm({ user, onEntrySaved }: FoodJournalFormProps) {
  // State to hold the form input values.
  // All fields that represent numbers (servings, protein_g, etc.) are initialized as strings,
  // because HTML input 'value' attributes always work with strings, and they will be parsed to numbers on save.
  const [entry, setEntry] = useState({
    date: new Date().toISOString().slice(0, 10), // Default to current date
    meal_type: '',
    food_name: '',
    servings: '1', // Changed to string
    serving_unit: '',
    protein_g: '', // Stored as string
    carbs_g: '',   // Stored as string
    fat_g: '',     // Stored as string
    calories: '',  // Stored as string
    mood: '',
    notes: ''
  });

  /**
   * Fetches nutrition data for a given food item from the /api/food-lookup endpoint.
   * Updates the form's protein, carbs, fat, and calories fields with the fetched data.
   * @param {string} food - The name of the food item to look up.
   */
  const fetchNutrition = async (food: string) => {
    try {
      const res = await fetch('/api/food-lookup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ food })
      });
      const data = await res.json();

      if (!data.error) {
        // IMPORTANT: Convert fetched numbers to strings before setting state,
        // as the state expects strings for these input fields.
        setEntry((prev) => ({
          ...prev,
          protein_g: data.protein_g != null ? String(data.protein_g) : '',
          carbs_g: data.carbs_g != null ? String(data.carbs_g) : '',
          fat_g: data.fat_g != null ? String(data.fat_g) : '',
          calories: data.calories != null ? String(data.calories) : ''
        }));
      } else {
        console.error('Nutrition lookup error:', data.error);
        // Optionally, clear fields or show an error message to the user
        setEntry((prev) => ({
          ...prev,
          protein_g: '',
          carbs_g: '',
          fat_g: '',
          calories: ''
        }));
      }
    } catch (error) {
      console.error('Failed to fetch nutrition data:', error);
      // Handle network or other errors, clear fields
      setEntry((prev) => ({
        ...prev,
        protein_g: '',
        carbs_g: '',
        fat_g: '',
        calories: ''
      }));
    }
  };

  /**
   * Handles the form submission, saving the food entry to Supabase.
   * Converts string input values for numerical fields back to numbers before saving.
   */
  const handleSave = async () => {
    if (!user) {
      // Use a custom modal or message box instead of alert in a real app
      console.error('User not logged in. Cannot save entry.');
      return;
    }

    try {
      // Parse string values from state to float numbers for Supabase insertion
      const { error } = await supabase.from('food_journal').insert({
        ...entry,
        user_id: user.id,
        // Explicitly parse to float, using 0 as a fallback for invalid numbers
        servings: parseFloat(entry.servings) || 0,
        protein_g: parseFloat(entry.protein_g) || 0,
        carbs_g: parseFloat(entry.carbs_g) || 0,
        fat_g: parseFloat(entry.fat_g) || 0,
        calories: parseFloat(entry.calories) || 0
      });

      if (error) {
        // Use a custom modal or message box for user feedback
        console.error('Error saving entry:', error.message);
      } else {
        onEntrySaved(); // Call the callback to signal successful save (e.g., to close modal and refresh table)
        // Reset only the food-related fields, keeping date and meal type for convenience if desired
        setEntry((prev) => ({
          ...prev, // Keep date and meal_type
          food_name: '',
          servings: '1', // Reset servings to string '1'
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
    <div className="space-y-4 p-4 rounded-lg bg-white shadow-inner"> {/* Added padding and background for better look */}
      <h3 className="text-xl font-semibold text-green-800 mb-4">Log Your Meal</h3>
      
      {/* Date Input */}
      <div>
        <label htmlFor="date" className="block text-gray-700 text-sm font-bold mb-1">Date:</label>
        <input
          type="date"
          name="date"
          id="date"
          value={entry.date}
          onChange={(e) => setEntry({ ...entry, date: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
        />
      </div>

      {/* Food Name Input with Nutrition Lookup */}
      <div>
        <label htmlFor="food_name" className="block text-gray-700 text-sm font-bold mb-1">Food Name:</label>
        <input
          type="text"
          name="food_name"
          id="food_name"
          value={entry.food_name}
          onChange={(e) => {
            const value = e.target.value;
            setEntry((prev) => ({ ...prev, food_name: value }));
            if (value.length >= 3) fetchNutrition(value); // Trigger lookup after 3 characters
          }}
          placeholder="e.g. oatmeal, chicken breast, apple"
          className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
        />
      </div>

      {/* Meal Type Dropdown */}
      <div>
        <label htmlFor="meal_type" className="block text-gray-700 text-sm font-bold mb-1">Meal Type:</label>
        <select
          name="meal_type"
          id="meal_type"
          value={entry.meal_type}
          onChange={(e) => setEntry({ ...entry, meal_type: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
        >
          <option value="">Select Meal Type</option>
          <option value="Breakfast">Breakfast</option>
          <option value="Lunch">Lunch</option>
          <option value="Dinner">Dinner</option>
          <option value="Snack">Snack</option>
        </select>
      </div>

      {/* Servings Input */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="servings" className="block text-gray-700 text-sm font-bold mb-1">Servings:</label>
          <input
            type="number"
            name="servings"
            id="servings"
            value={entry.servings} // Bind to string value
            onChange={(e) => setEntry({ ...entry, servings: e.target.value })}
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
            placeholder="e.g. 1, 0.5"
            step="0.1" // Allow decimal servings
          />
        </div>
        <div>
          <label htmlFor="serving_unit" className="block text-gray-700 text-sm font-bold mb-1">Unit:</label>
          <select
            name="serving_unit"
            id="serving_unit"
            value={entry.serving_unit}
            onChange={(e) => setEntry({ ...entry, serving_unit: e.target.value })}
            className="w-full p-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
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
      </div>

      {/* Nutritional Info (Read-only, populated by API) */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-gray-700 text-sm font-bold mb-1">Protein (g):</label>
          <input
            type="text" // Keep as text, as it's primarily display/API-driven
            value={entry.protein_g}
            readOnly // Make read-only as it's populated by lookup
            className="w-full p-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 cursor-not-allowed"
          />
        </div>
        <div>
          <label className="block text-gray-700 text-sm font-bold mb-1">Carbs (g):</label>
          <input
            type="text" // Keep as text
            value={entry.carbs_g}
            readOnly
            className="w-full p-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 cursor-not-allowed"
          />
        </div>
        <div>
          <label className="block text-gray-700 text-sm font-bold mb-1">Fat (g):</label>
          <input
            type="text" // Keep as text
            value={entry.fat_g}
            readOnly
            className="w-full p-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 cursor-not-allowed"
          />
        </div>
        <div>
          <label className="block text-gray-700 text-sm font-bold mb-1">Calories:</label>
          <input
            type="text" // Keep as text
            value={entry.calories}
            readOnly
            className="w-full p-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 cursor-not-allowed"
          />
        </div>
      </div>

      {/* Mood Dropdown */}
      <div>
        <label htmlFor="mood" className="block text-gray-700 text-sm font-bold mb-1">Mood:</label>
        <select
          name="mood"
          id="mood"
          value={entry.mood}
          onChange={(e) => setEntry({ ...entry, mood: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
        >
          <option value="">Select Mood</option>
          <option value="Sad">Sad</option>
          <option value="Okay">Okay</option>
          <option value="Good">Good</option>
          <option value="Great">Great</option>
        </select>
      </div>

      {/* Notes Textarea */}
      <div>
        <label htmlFor="notes" className="block text-gray-700 text-sm font-bold mb-1">Notes:</label>
        <textarea
          name="notes"
          id="notes"
          value={entry.notes}
          onChange={(e) => setEntry({ ...entry, notes: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors resize-y min-h-[80px]"
          placeholder="Add any additional notes about your meal or feelings..."
        />
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className="text-white font-bold bg-green-700 p-3 rounded-lg hover:bg-green-800 transition-colors w-full shadow-md mt-4"
      >
        Save Entry
      </button>
    </div>
  );
}
