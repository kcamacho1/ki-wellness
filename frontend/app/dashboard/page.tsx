"use client";
// app/dashboard/page.tsx
import { useState } from "react";
import DashboardPanel from "@/components/DashboardPanel";
import AISidebar from "@/components/AISidebar";
import {
  Notebook,
  BarChart3,
  BrainCircuit,
  BookOpen,
  Dumbbell,
  Sparkles,
} from "lucide-react";

export default function DashboardPage() {
  const [activePanel, setActivePanel] = useState("AIAnalysis");

  return (
    <main className="min-h-screen bg-green-900 text-green-700 p-6 space-y-4 font-inter">
      <section className="max-w-6xl mx-auto bg-amber-50 p-6 rounded-xl shadow text-gray-800">
        <h1 className="text-4xl font-bold text-green-800 papyrus mb-2">
          your dashboard
        </h1>
        <p className="text-gray-700">
          Keep it Simple ~ Stay on Track ~ Journal your food, track your wellness, and analyze nutrition.
        </p>
      </section>

      <section className="max-w-6xl mx-auto bg-amber-50 p-6 rounded-xl shadow text-gray-800 space-y-6">

        {/* Personal Trainer AI Assistant */}
        <div className="flex justify-center">
          <AISidebar currentPanel={activePanel} />
        </div>

        {/* Top collapsed panels */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <DashboardPanel
            title="Recipe Book"
            icon={<BookOpen />}
            onActivate={setActivePanel}
          >
            <div>Recipe Book content here.</div>
          </DashboardPanel>
          <DashboardPanel
            title="Exercise Playlist"
            icon={<Dumbbell />}
            onActivate={setActivePanel}
          >
            <div>Exercise Playlist content here.</div>
          </DashboardPanel>
          <DashboardPanel
            title="Spiritual Playlist"
            icon={<Sparkles />}
            onActivate={setActivePanel}
          >
            <div>Spiritual Playlist content here.</div>
          </DashboardPanel>
        </div>

        {/* Always expanded panels */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <DashboardPanel
            title="Food Journal"
            icon={<Notebook />}
            defaultExpanded
            onActivate={setActivePanel}
          >
            <div>Food Journal content here.</div>
          </DashboardPanel>
          <DashboardPanel
            title="Charts"
            icon={<BarChart3 />}
            defaultExpanded
            onActivate={setActivePanel}
          >
            <div>Charts content here.</div>
          </DashboardPanel>
          <DashboardPanel
            title="AI Analysis"
            icon={<BrainCircuit />}
            defaultExpanded
            onActivate={setActivePanel}
          >
            <div>AI Analysis content here.</div>
          </DashboardPanel>
        </div>
      </section>
    </main>
  );
}
