// src/components/DashboardHeader.tsx
'use client';

import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

export default function DashboardHeader() {
  const router = useRouter();

  return (
    <section className="max-w-6xl mx-auto text-center border-2 border-green-900 rounded-xl p-6 bg-amber-50 text-gray-800">
      <div className="text-right">
        <button
          onClick={async () => {
            await supabase.auth.signOut();
            router.push('/login');
          }}
          className="text-sm text-green-800 underline hover:text-red-600"
        >
          Log out
        </button>
      </div>
      <h1 className="text-4xl font-bold text-green-800 papyrus mb-4">your dashboard</h1>
      <p className="text-lg text-gray-700">Journal your food, save meals, favorite exercises and spiritual videos.</p>
      <p>Set reminders and stay balanced 🧘</p>
    </section>
  );
}
