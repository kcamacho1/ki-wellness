'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';
import { createClient } from '@supabase/supabase-js'


export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent form refresh
    setLoading(true);

    const { error } = isLogin
      ? await supabase.auth.signInWithPassword({ email, password })
      : await supabase.auth.signUp({ email, password });

    if (error) {
      alert(error.message);
      setLoading(false);
    } else {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        router.push('/dashboard');
      } else {
        alert('Check your email to verify your account.');
      }
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-green-900 text-gray-100 font-sans p-6 flex justify-center items-center">
      <div className="bg-amber-50 text-gray-800 rounded-xl p-6 w-full max-w-md shadow-md space-y-4">
        <h1 className="text-2xl font-bold text-green-800 text-center papyrus">
          {isLogin ? 'Log in to Ki Wellness' : 'Create Your Account'}
        </h1>

        <form onSubmit={handleAuth} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2 border bg-white rounded text-black"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full p-2 bg-white border rounded text-black"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 px-6 py-2 rounded hover:bg-green-700"
          >
            {loading ? 'Please wait...' : isLogin ? 'Log In' : 'Sign Up'}
          </button>
        </form>

        <p className="text-sm text-center">
          {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="underline text-green hover:text-green-300"
          >
            {isLogin ? 'Sign up' : 'Log in'}
          </button>
        </p>
      </div>
    </main>
  );
}

