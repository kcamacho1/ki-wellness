"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
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
      setUser(currentUser);

      if (!currentUser) {
        router.push("/login");
        return;
      }

      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("user_id", currentUser.id)
        .single();

      if (error && error.code !== "PGRST116") {
        // Not found error is okay (new user)
        console.error(error);
        setError("Error loading profile.");
      }

      if (data) {
        setFormData({
          ...formData,
          ...data,
        });
      }

      setLoading(false);
    };

    loadProfile();
  }, [router]);

  const handleSave = async () => {
    if (!user) return;
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
            src={user.user_metadata?.avatar_url || "/default-avatar.png"}
            alt="Profile"
            width={100}
            height={100}
            className="rounded-full border border-green-700"
          />
          <h1 className="text-2xl font-bold text-green-800 papyrus">
            {formData.name || "Your Profile"}
          </h1>
          <p className="text-sm text-gray-600">{user.email}</p>
        </div>

        {error && <p className="text-red-600">{error}</p>}

        <form className="space-y-4">
          {Object.entries(formData).map(([key, value]) => (
            <textarea
              key={key}
              placeholder={key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
              value={value}
              onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          ))}
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
