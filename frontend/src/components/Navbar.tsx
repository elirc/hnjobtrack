"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import { User } from "@supabase/supabase-js";
import { Briefcase, Bookmark, UserCircle, LogOut } from "lucide-react";

export function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const supabase = createClient();

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user));

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    window.location.href = "/";
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-hn rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">HN</span>
              </div>
              <span className="font-bold text-lg text-gray-900">Jobs</span>
            </Link>

            <div className="hidden sm:flex items-center gap-1">
              <Link
                href="/dashboard"
                className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <Briefcase size={16} />
                Browse
              </Link>
              {user && (
                <>
                  <Link
                    href="/dashboard/for-you"
                    className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    For You
                  </Link>
                  <Link
                    href="/saved"
                    className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <Bookmark size={16} />
                    Saved
                  </Link>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <Link
                  href="/profile"
                  className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <UserCircle size={16} />
                  <span className="hidden sm:inline">Profile</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <LogOut size={16} />
                  <span className="hidden sm:inline">Log out</span>
                </button>
              </>
            ) : (
              <>
                <Link href="/auth/login" className="btn-secondary text-sm">
                  Log in
                </Link>
                <Link href="/auth/signup" className="btn-primary text-sm">
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
