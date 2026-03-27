"use client";

import { useState, useEffect } from "react";
import { Search, MapPin, Briefcase, Heart, MessageCircle, Filter, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Send } from "lucide-react";

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

const COUNTRIES = ["全部", "德国", "法国", "英国", "荷兰", "西班牙", "意大利", "瑞典", "瑞士", "芬兰", "波兰", "丹麦", "挪威", "奥地利", "比利时", "爱尔兰", "捷克", "葡萄牙", "希腊"];
const CATEGORIES = ["全部", "技术", "产品设计", "金融", "市场", "销售", "人力资源", "运营", "医疗", "教育", "制造工程", "行政", "法律", "房地产", "其他"];

const ITEMS_PER_PAGE = 20;

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("全部");
  const [selectedCategory, setSelectedCategory] = useState("全部");
  const [likedJobs, setLikedJobs] = useState<Set<number>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedJob, setExpandedJob] = useState<number | null>(null);

  useEffect(() => {
    fetchAllJobs();
  }, []);

  const fetchAllJobs = async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://eurojobs-production.up.railway.app';
      const res = await fetch(`${apiUrl}/api/jobs`);
      const data = await res.json();
      setJobs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
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

  const totalPages = Math.ceil(filteredJobs.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedJobs = filteredJobs.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleLike = async (jobId: number) => {
    const userStr = localStorage.getItem("user");
    if (!userStr) {
      window.location.href = "/login";
      return;
    }

    if (likedJobs.has(jobId)) {
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://eurojobs-production.up.railway.app';
      const token = localStorage.getItem("token");
      const res = await fetch(`${apiUrl}/api/jobs/${jobId}/like`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setJobs(jobs.map(j => j.id === jobId ? { ...j, likes: data.likes } : j));
        setLikedJobs(new Set(likedJobs.add(jobId)));
      }
    } catch (error) {
      console.error("Failed to like job:", error);
    }
  };

  const toggleExpand = (jobId: number) => {
    setExpandedJob(expandedJob === jobId ? null : jobId);
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-12">
        <div className="container">
          <h2 className="text-3xl font-bold mb-4">探索欧洲优质工作</h2>
          <p className="text-lg text-primary-100 mb-6">整合全欧招聘信息，助您找到理想岗位</p>

          {/* Search Bar */}
          <div className="flex gap-4 max-w-2xl">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="搜索职位、公司..."
                className="w-full pl-10 pr-4 py-3 rounded-lg text-gray-900"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="bg-white py-4 border-b sticky top-0 z-10">
        <div className="container">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-gray-500" />
              <span className="font-medium text-gray-700">筛选:</span>
            </div>

            <select
              className="px-3 py-2 border rounded-lg bg-white text-sm"
              value={selectedCountry}
              onChange={(e) => { setSelectedCountry(e.target.value); setCurrentPage(1); }}
            >
              {COUNTRIES.map((c) => (
                <option key={c} value={c}>{c === "全部" ? "全部国家" : c}</option>
              ))}
            </select>

            <select
              className="px-3 py-2 border rounded-lg bg-white text-sm"
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setCurrentPage(1); }}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c === "全部" ? "全部类别" : c}</option>
              ))}
            </select>

            <span className="text-gray-500 ml-auto">
              共 {filteredJobs.length} 个职位
            </span>
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
          ) : paginatedJobs.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <Briefcase size={48} className="mx-auto mb-4 opacity-50" />
              <p>暂无职位</p>
            </div>
          ) : (
            <>
              <div className="grid gap-4">
                {paginatedJobs.map((job) => (
                  <div key={job.id} className="bg-white p-5 rounded-lg shadow-sm border hover:shadow-md transition">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3
                          className="text-lg font-semibold text-gray-900 mb-1 cursor-pointer hover:text-primary-600 flex items-center gap-2"
                          onClick={() => toggleExpand(job.id)}
                        >
                          {job.title}
                          {expandedJob === job.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </h3>
                        <p className="text-gray-600 mb-2">{job.company}</p>
                        <div className="flex flex-wrap gap-3 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <MapPin size={14} /> {job.location || job.country}
                          </span>
                          <span className="flex items-center gap-1">
                            <Briefcase size={14} /> {job.category}
                          </span>
                          {job.salary_range && (
                            <span className="text-green-600 text-sm">{job.salary_range}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col gap-2 ml-4">
                        <button
                          onClick={() => handleLike(job.id)}
                          disabled={likedJobs.has(job.id)}
                          className={`flex items-center gap-1 px-3 py-1 rounded text-sm ${
                            likedJobs.has(job.id)
                              ? "bg-red-50 text-red-500 cursor-not-allowed"
                              : "bg-gray-50 text-gray-500 hover:bg-gray-100"
                          }`}
                        >
                          <Heart size={14} fill={likedJobs.has(job.id) ? "currentColor" : "none"} />
                          {job.likes}
                        </button>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {expandedJob === job.id && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <h4 className="font-semibold mb-2">职位描述</h4>
                          <p className="text-gray-700 whitespace-pre-line text-sm mb-4">
                            {job.description || "暂无详细描述"}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                            <span>来源: {job.source}</span>
                            <span>发布日期: {new Date(job.created_at).toLocaleDateString('zh-CN')}</span>
                          </div>
                          <a
                            href={`/apply?jobId=${job.id}&title=${encodeURIComponent(job.title)}&company=${encodeURIComponent(job.company)}`}
                            className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
                          >
                            <Send size={16} /> 申请职位
                          </a>
                        </div>
                      </div>
                    )}

                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-xs text-gray-400">来源: {job.source}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center items-center gap-4 mt-8">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="flex items-center gap-1 px-4 py-2 rounded-lg bg-white border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft size={18} /> 上一页
                  </button>
                  <span className="text-gray-600">
                    第 {currentPage} / {totalPages} 页
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="flex items-center gap-1 px-4 py-2 rounded-lg bg-white border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    下一页 <ChevronRight size={18} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
}