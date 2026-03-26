import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "EuroJobs - 欧洲招聘平台",
  description: "整合欧洲各国招聘信息，一站式求职平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <header className="bg-white shadow-sm border-b">
          <div className="container py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-primary-600">EuroJobs</h1>
              <nav className="flex gap-6">
                <a href="/" className="text-gray-600 hover:text-primary-600">首页</a>
                <a href="/jobs" className="text-gray-600 hover:text-primary-600">职位</a>
              </nav>
            </div>
          </div>
        </header>
        <main>{children}</main>
        <footer className="bg-gray-900 text-white py-8 mt-16">
          <div className="container text-center">
            <p>&copy; 2024 EuroJobs. All rights reserved.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}