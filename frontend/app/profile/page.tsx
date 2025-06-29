"use client";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: "",
    dob: "",
    weight: "",
    height: "",
    goals: "",
    ailments: "",
    dailyActivities: "",
    sleepSchedule: "",
    dietaryPreferences: "",
    dietaryRestrictions: "",
    spiritualBeliefs: "",
    connectSelf: "",
    connectSurroundings: "",
    provideOthers: "",
    safeGroups: "",
    awe: "",
    creativeExpression: "",
    handlingUpset: "",
    notes: "",
  });

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      const currentUser = data.session?.user ?? null;
      setUser(currentUser);

      if (!currentUser) {
        router.push("/login");
      }
    });
  }, [router]);

  if (!user) {
    return null;
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
            {user.user_metadata?.full_name || "Your Profile"}
          </h1>
          <p className="text-sm text-gray-600">{user.email}</p>
        </div>

        <form className="space-y-4">
          <input
            type="text"
            placeholder="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            type="date"
            placeholder="Date of Birth"
            value={formData.dob}
            onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              type="text"
              placeholder="Weight"
              value={formData.weight}
              onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
              className="border border-gray-300 rounded px-3 py-2"
            />
            <input
              type="text"
              placeholder="Height"
              value={formData.height}
              onChange={(e) => setFormData({ ...formData, height: e.target.value })}
              className="border border-gray-300 rounded px-3 py-2"
            />
          </div>
          <textarea
            placeholder="Daily Goals"
            value={formData.goals}
            onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Ailments"
            value={formData.ailments}
            onChange={(e) => setFormData({ ...formData, ailments: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Daily Activities"
            value={formData.dailyActivities}
            onChange={(e) => setFormData({ ...formData, dailyActivities: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            type="text"
            placeholder="Sleep Schedule"
            value={formData.sleepSchedule}
            onChange={(e) => setFormData({ ...formData, sleepSchedule: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            type="text"
            placeholder="Dietary Preferences"
            value={formData.dietaryPreferences}
            onChange={(e) =>
              setFormData({ ...formData, dietaryPreferences: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            type="text"
            placeholder="Dietary Restrictions"
            value={formData.dietaryRestrictions}
            onChange={(e) =>
              setFormData({ ...formData, dietaryRestrictions: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Spiritual Beliefs"
            value={formData.spiritualBeliefs}
            onChange={(e) =>
              setFormData({ ...formData, spiritualBeliefs: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="How I enjoy connecting with myself"
            value={formData.connectSelf}
            onChange={(e) => setFormData({ ...formData, connectSelf: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="How I connect with my surroundings"
            value={formData.connectSurroundings}
            onChange={(e) =>
              setFormData({ ...formData, connectSurroundings: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="What I enjoy providing to others"
            value={formData.provideOthers}
            onChange={(e) =>
              setFormData({ ...formData, provideOthers: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Groups I feel safe in"
            value={formData.safeGroups}
            onChange={(e) =>
              setFormData({ ...formData, safeGroups: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Things that make me feel awe"
            value={formData.awe}
            onChange={(e) => setFormData({ ...formData, awe: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Creative ways I express myself"
            value={formData.creativeExpression}
            onChange={(e) =>
              setFormData({ ...formData, creativeExpression: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="How I handle upsetting situations"
            value={formData.handlingUpset}
            onChange={(e) =>
              setFormData({ ...formData, handlingUpset: e.target.value })
            }
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <textarea
            placeholder="Additional Notes / Goals"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
        </form>
      </section>
    </main>
  );
}
