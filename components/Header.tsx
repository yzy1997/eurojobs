"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();
  const [user, setUser] = useState<{ username: string } | null>(null);

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      setUser(JSON.parse(userStr));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    router.push("/");
  };

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary-600">
            <Link href="/">EuroJobs</Link>
          </h1>
          <nav className="flex gap-6 items-center">
            <Link href="/" className="text-gray-600 hover:text-primary-600">
              首页
            </Link>
            {user ? (
              <>
                <span className="text-gray-600">欢迎, {user.username}</span>
                <button
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-primary-600"
                >
                  退出
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="text-gray-600 hover:text-primary-600">
                  登录
                </Link>
                <Link
                  href="/register"
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                >
                  注册
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}