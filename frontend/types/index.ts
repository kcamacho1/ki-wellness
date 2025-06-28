export interface FoodJournalEntry {
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
}

export interface User {
  id: string;
  email: string;
}
