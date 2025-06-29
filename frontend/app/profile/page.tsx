"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import Image from "next/image";
import type { User } from "@supabase/supabase-js";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    dob: "",
    weight: "",
    height: "",
    goals: "",
    ailments: "",
    daily_activities: "",
    sleep_schedule: "",
    dietary_preferences: "",
    dietary_restrictions: "",
    spiritual_beliefs: "",
    connect_self: "",
    connect_surroundings: "",
    provide_others: "",
    safe_groups: "",
    awe: "",
    creative_expression: "",
    handling_upset: "",
    notes: "",
  });

  useEffect(() => {
    const loadProfile = async () => {
      const { data: sessionData } = await supabase.auth.getSession();
      const currentUser = sessionData.session?.user ?? null;

      if (!currentUser) {
        router.push("/login");
        return;
      }

      setUser(currentUser);

      const { data, error, status } = await supabase
        .from("profiles")
        .select("*")
        .eq("user_id", currentUser.id)
        .single();

      if (error && status !== 406) {
        console.error(error);
        setError("Error loading profile.");
      }

      if (data) {
        setFormData((prev) => ({
          ...prev,
          ...data,
        }));
      }

      setLoading(false);
    };

    loadProfile();
  }, [router]);

  const handleSave = async () => {
    if (!user) {
      throw new Error("User is not authenticated");
    }
    setSaving(true);
    setError("");

    const { error } = await supabase
      .from("profiles")
      .upsert({
        user_id: user.id,
        ...formData,
      });

    if (error) {
      console.error(error);
      setError("Error saving profile.");
    } else {
      alert("Profile saved!");
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p>Loading profile...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-green-50 text-gray-800 font-sans p-6">
      <section className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow space-y-4">
        <div className="flex flex-col items-center space-y-2">
          <Image
            src={user?.user_metadata?.avatar_url || "/default-avatar.png"}
            alt="Profile"
            width={100}
            height={100}
            className="rounded-full border border-green-700"
          />
          <h1 className="text-2xl font-bold text-green-800 papyrus">
            {formData.name || "Your Profile"}
          </h1>
            <p className="text-sm text-gray-600">{user?.email}</p>
        </div>

        {error && <p className="text-red-600">{error}</p>}

        <form className="space-y-6">
          {/* Basic Info */}
          <div>
            <h2 className="text-lg font-semibold text-green-800 mb-2">
              Basic Information
            </h2>
            <label className="block text-sm text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className="w-full border border-gray-300 rounded px-3 py-2 mb-3"
            />

            <label className="block text-sm text-gray-700 mb-1">Date of Birth</label>
            <input
              type="date"
              value={formData.dob}
              onChange={(e) =>
                setFormData({ ...formData, dob: e.target.value })
              }
              className="w-full border border-gray-300 rounded px-3 py-2 mb-3"
            />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">Weight</label>
                <input
                  type="text"
                  value={formData.weight}
                  onChange={(e) =>
                    setFormData({ ...formData, weight: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">Height</label>
                <input
                  type="text"
                  value={formData.height}
                  onChange={(e) =>
                    setFormData({ ...formData, height: e.target.value })
                  }
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
            </div>
          </div>

          {/* You can keep the rest of your sections unchanged */}
          {/* ...Goals & Ailments, Lifestyle, Spiritual & Reflection, Notes... */}

          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
          >
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </section>
    </main>
  );
}
