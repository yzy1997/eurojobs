"use client";

import { useState, useEffect } from "react";
import { Search, MapPin, Briefcase, Heart, MessageCircle, Filter } from "lucide-react";

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  country: string;
  category: string;
  salary_range: string;
  description: string;
  url: string;
  source: string;
  likes: number;
  created_at: string;
}

const COUNTRIES = ["全部", "德国", "法国", "英国", "荷兰", "西班牙", "意大利", "瑞典", "瑞士"];
const CATEGORIES = ["全部", "技术", "金融", "市场", "销售", "设计", "运营", "人力"];

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("全部");
  const [selectedCategory, setSelectedCategory] = useState("全部");
  const [likedJobs, setLikedJobs] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const res = await fetch("/api/jobs");
      const data = await res.json();
      // 确保 data 是数组
      setJobs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter((job) => {
    const matchSearch = job.title.toLowerCase().includes(search.toLowerCase()) ||
                       job.company.toLowerCase().includes(search.toLowerCase());
    const matchCountry = selectedCountry === "全部" || job.country === selectedCountry;
    const matchCategory = selectedCategory === "全部" || job.category === selectedCategory;
    return matchSearch && matchCountry && matchCategory;
  });

  const handleLike = async (jobId: number) => {
    try {
      await fetch(`/api/jobs/${jobId}/like`, { method: "POST" });
      setJobs(jobs.map(j => j.id === jobId ? { ...j, likes: j.likes + 1 } : j));
      setLikedJobs(new Set(likedJobs.add(jobId)));
    } catch (error) {
      console.error("Failed to like job:", error);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-16">
        <div className="container">
          <h2 className="text-4xl font-bold mb-4">探索欧洲优质工作</h2>
          <p className="text-xl text-primary-100 mb-8">整合全欧招聘信息，助您找到理想岗位</p>

          {/* Search Bar */}
          <div className="flex gap-4 max-w-2xl">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="搜索职位、公司..."
                className="w-full pl-10 pr-4 py-3 rounded-lg text-gray-900"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="bg-white py-6 border-b">
        <div className="container">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter size={20} className="text-gray-500" />
              <span className="font-medium text-gray-700">筛选:</span>
            </div>

            <select
              className="px-4 py-2 border rounded-lg bg-white"
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
            >
              {COUNTRIES.map((c) => (
                <option key={c} value={c}>{c === "全部" ? "全部国家" : c}</option>
              ))}
            </select>

            <select
              className="px-4 py-2 border rounded-lg bg-white"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c === "全部" ? "全部类别" : c}</option>
              ))}
            </select>

            <span className="text-gray-500 ml-auto">共 {filteredJobs.length} 个职位</span>
          </div>
        </div>
      </section>

      {/* Job List */}
      <section className="py-8">
        <div className="container">
          {loading ? (
            <div className="text-center py-16">
              <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto"></div>
              <p className="mt-4 text-gray-500">加载中...</p>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <Briefcase size={48} className="mx-auto mb-4 opacity-50" />
              <p>暂无职位</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredJobs.map((job) => (
                <div key={job.id} className="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        <a href={`/jobs/${job.id}`} className="hover:text-primary-600">
                          {job.title}
                        </a>
                      </h3>
                      <p className="text-gray-600 mb-2">{job.company}</p>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <MapPin size={16} /> {job.location}, {job.country}
                        </span>
                        <span className="flex items-center gap-1">
                          <Briefcase size={16} /> {job.category}
                        </span>
                        {job.salary_range && (
                          <span className="text-green-600">{job.salary_range}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2 ml-4">
                      <button
                        onClick={() => handleLike(job.id)}
                        className={`flex items-center gap-1 px-3 py-1 rounded ${
                          likedJobs.has(job.id)
                            ? "bg-red-50 text-red-500"
                            : "bg-gray-50 text-gray-500 hover:bg-gray-100"
                        }`}
                      >
                        <Heart size={16} fill={likedJobs.has(job.id) ? "currentColor" : "none"} />
                        {job.likes}
                      </button>
                      <a
                        href={`/jobs/${job.id}`}
                        className="flex items-center gap-1 px-3 py-1 rounded bg-gray-50 text-gray-500 hover:bg-gray-100"
                      >
                        <MessageCircle size={16} /> 评论
                      </a>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-xs text-gray-400">来源: {job.source}</span>
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:underline text-sm"
                    >
                      查看原站 →
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Ad Space */}
      <section className="py-8 bg-gray-50">
        <div className="container">
          <div className="bg-white rounded-lg p-8 text-center border-2 border-dashed border-gray-300">
            <p className="text-gray-400">广告位招商中...</p>
          </div>
        </div>
      </section>
    </div>
  );
}