"use client";

export default function AISidebar({
  currentPanel,
}: {
  currentPanel: string;
}) {
  const messages: Record<string, string> = {
    FoodJournal: "Here are some AI suggestions for your meals!",
    Charts: "Analyzing your wellness trends...",
    RecipeBook: "How about trying a new recipe today?",
    ExercisePlaylist: "Stay active! Here are some workouts.",
    SpiritualPlaylist: "Align your mind and spirit.",
    AIAnalysis: "Overall analysis and insights.",
  };

  return (
    <aside className="hidden lg:block w-lg p-4 bg-white border rounded-lg shadow space-y-2">
      <h2 className="text-xl font-bold text-green-800 flex gap-2">
        🤖 Personal Trainer
      </h2>
      <p className="text-gray-700">{messages[currentPanel]}</p>
    </aside>
  );
}
