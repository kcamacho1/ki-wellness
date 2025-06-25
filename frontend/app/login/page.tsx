'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    setLoading(true);

    let authResponse;
    if (isLogin) {
      authResponse = await supabase.auth.signInWithPassword({ email, password });
    } else {
      authResponse = await supabase.auth.signUp({ email, password });
    }

    const { error } = authResponse;

    if (error) {
      alert(error.message);
      setLoading(false);
      return;
    }

    const { data: sessionData } = await supabase.auth.getSession();

    if (sessionData.session) {
      router.push('/dashboard'); // ✅ change if your dashboard route is different
    } else {
      alert('Check your email to verify your account.');
    }

    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-green-900 text-gray-100 font-sans p-6 flex justify-center items-center">
      <div className="bg-amber-50 text-gray-800 rounded-xl p-6 w-full max-w-md shadow-md space-y-4">
        <h1 className="text-2xl font-bold text-green-800 text-center papyrus">
          {isLogin ? 'Log in to Ki Wellness' : 'Create Your Account'}
        </h1>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-2 border bg-white rounded text-black"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 border bg-white rounded text-black"
        />

        <button
          onClick={handleAuth}
          disabled={loading}
          className="w-full bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
        >
          {loading ? 'Please wait...' : isLogin ? 'Log In' : 'Sign Up'}
        </button>

        <p className="text-sm text-center">
          {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="underline text-green-800 hover:text-green-600"
          >
            {isLogin ? 'Sign up' : 'Log in'}
          </button>
        </p>
      </div>
    </main>
  );
}
