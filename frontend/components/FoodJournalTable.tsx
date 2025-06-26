'use client';

import React from 'react';

type Entry = {
  id: string;
  date: string;
  food_name: string;
  servings: number;
  serving_unit: string;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  calories: number;
};

type Props = {
  entries: Entry[];
};

export default function FoodJournalTable({ entries }: Props) {
  return (
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
          {entries.map((entry) => (
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
  );
}
