"use client";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import type { User } from "@supabase/auth-js";
import { Menu } from "@headlessui/react";


export default function Header() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  return (
    <header className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center p-6">
      <div className="flex items-center space-x-4">
        <Link href="/" className="hover:underline">
          <Image
            src="/logoname.png"
            alt="Ki Wellness Logo"
            width={180}
            height={60}
            className="rounded"
          />
        </Link>
      </div>
            <nav className="flex flex-wrap gap-4 text-green-900 text-sm md:text-base font-medium mt-4 md:mt-0">
            {user ? (
                <Menu as="div" className="relative inline-block text-left">
                <Menu.Button className="flex items-center space-x-2 hover:opacity-80 transition">
                    <Image
                    src={user.user_metadata?.avatar_url || "/default-avatar.png"}
                    alt="Profile"
                    width={36}
                    height={36}
                    className="rounded-full border border-green-700"
                    />
                </Menu.Button>
                <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right bg-white border border-gray-200 rounded-md shadow-lg focus:outline-none z-50">
                    <div className="p-3 border-b border-gray-100">
                    <p className="text-sm text-gray-700">{user.email}</p>
                    </div>
                    <div className="py-1">
                    <Menu.Item>
                        {({ active }) => (
                        <Link
                            href="/profile"
                            className={`block px-4 py-2 text-sm ${
                            active ? "bg-green-50 text-green-800" : "text-gray-700"
                            }`}
                        >
                            Profile
                        </Link>
                        )}
                    </Menu.Item>
                    <Menu.Item>
                        {({ active }) => (
                        <Link
                            href="/settings"
                            className={`block px-4 py-2 text-sm ${
                            active ? "bg-green-50 text-green-800" : "text-gray-700"
                            }`}
                        >
                            Settings
                        </Link>
                        )}
                    </Menu.Item>
                    <Menu.Item>
                        {({ active }) => (
                        <button
                            onClick={() => supabase.auth.signOut()}
                            className={`block w-full text-left px-4 py-2 text-sm ${
                            active ? "bg-green-50 text-red-700" : "text-red-600"
                            }`}
                        >
                            Sign Out
                        </button>
                        )}
                    </Menu.Item>
                    </div>
                </Menu.Items>
                </Menu>
            ) : (
                <>
                <Link href="/about" className="hover:underline">
                    About
                </Link>
                <Link href="/pricing" className="hover:underline">
                    Services & Pricing
                </Link>
                <Link href="/resources" className="hover:underline">
                    Free Resources
                </Link>
                <Link href="/login" className="text-green-700 hover:underline font-semibold">
                    Sign In
                </Link>
                </>
            )}
            </nav>

    </header>
  );
}
