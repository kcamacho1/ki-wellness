"use client";
import { useEffect, useState } from "react";

export default function FoodJournal() {
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    const fetchEntries = async () => {
      const res = await fetch("/api/food-entries"); // or your FastAPI URL
      const data = await res.json();
      setEntries(data);
    };
    fetchEntries();
  }, []);

  return (
    <div className="space-y-2">
Food Journal
    </div>
  );
}
