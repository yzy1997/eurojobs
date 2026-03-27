"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { User, Mail, Phone, MapPin, Briefcase, GraduationCap, Send, FileText, ArrowLeft } from "lucide-react";

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  country: string;
  email?: string;
}

function ApplyContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);

  // Form data
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    location: "",
    education: "",
    experience: "",
    skills: "",
    coverLetter: ""
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const jobId = searchParams.get("jobId");
    const title = searchParams.get("title");
    const company = searchParams.get("company");

    if (jobId && title && company) {
      setJob({
        id: Number(jobId),
        title: decodeURIComponent(title),
        company: decodeURIComponent(company),
        location: "",
        country: ""
      });

      // 如果已登录，填充用户信息
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const user = JSON.parse(userStr);
        setFormData(prev => ({ ...prev, name: user.username }));
      }
    }
    setLoading(false);
  }, [searchParams]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const generateResume = () => {
    return `
个人简历
===========

基本信息
--------
姓名: ${formData.name}
邮箱: ${formData.email}
电话: ${formData.phone}
所在地: ${formData.location}

教育背景
--------
${formData.education || "暂无"}

工作经历
--------
${formData.experience || "暂无"}

技能专长
--------
${formData.skills || "暂无"}

求职意向
--------
应聘职位: ${job?.title}
公司: ${job?.company}

---
来自 EuroJobs 求职平台
    `.trim();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    // 模拟提交（实际应该发送到后端）
    await new Promise(resolve => setTimeout(resolve, 1500));

    // 保存申请记录到后端
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://eurojobs-production.up.railway.app';
      const token = localStorage.getItem("token");

      await fetch(`${apiUrl}/api/applications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          job_id: job?.id,
          job_title: job?.title,
          company: job?.company,
          ...formData
        })
      });
    } catch (error) {
      console.error("Failed to save application:", error);
    }

    setSubmitted(true);
    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">无效的职位申请链接</p>
          <a href="/" className="text-primary-600 hover:underline">返回首页</a>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">申请提交成功！</h2>
            <p className="text-gray-500 mb-6">
              您的申请已成功提交，我们已将您的简历发送到招聘方。
            </p>
            <div className="bg-gray-50 p-4 rounded-lg text-left mb-6">
              <p className="text-sm text-gray-500 mb-2">申请职位</p>
              <p className="font-semibold">{job.title}</p>
              <p className="text-gray-600">{job.company}</p>
            </div>
            <a
              href="/"
              className="block w-full bg-primary-600 text-white py-3 rounded-lg hover:bg-primary-700"
            >
              返回首页
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="container">
        <a href="/" className="inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6">
          <ArrowLeft size={20} /> 返回
        </a>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Application Form */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h1 className="text-2xl font-bold mb-2">申请职位</h1>
              <div className="bg-primary-50 p-4 rounded-lg mb-6">
                <h2 className="font-semibold text-primary-900">{job.title}</h2>
                <p className="text-primary-700">{job.company}</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <h3 className="font-semibold text-lg border-b pb-2">基本信息</h3>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      姓名 *
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="pl-10 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      邮箱 *
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="pl-10 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      电话
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        className="pl-10 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      所在地
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                      <input
                        type="text"
                        name="location"
                        value={formData.location}
                        onChange={handleChange}
                        className="pl-10 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                        placeholder="城市, 国家"
                      />
                    </div>
                  </div>
                </div>

                <h3 className="font-semibold text-lg border-b pb-2 pt-4">教育背景</h3>
                <div>
                  <div className="relative">
                    <GraduationCap className="absolute left-3 top-3 text-gray-400" size={18} />
                    <textarea
                      name="education"
                      value={formData.education}
                      onChange={handleChange}
                      rows={3}
                      className="pl-10 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                      placeholder="例如：2020-2024 XX大学 计算机科学学士"
                    />
                  </div>
                </div>

                <h3 className="font-semibold text-lg border-b pb-2 pt-4">工作经历</h3>
                <div>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-3 text-gray-400" size={18} />
                    <textarea
                      name="experience"
                      value={formData.experience}
                      onChange={handleChange}
                      rows={4}
                      className="pl-10 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                      placeholder="请描述您的工作经历..."
                    />
                  </div>
                </div>

                <h3 className="font-semibold text-lg border-b pb-2 pt-4">技能专长</h3>
                <div>
                  <textarea
                    name="skills"
                    value={formData.skills}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    placeholder="例如：Python, JavaScript, React, Node.js, SQL..."
                  />
                </div>

                <h3 className="font-semibold text-lg border-b pb-2 pt-4">求职信</h3>
                <div>
                  <textarea
                    name="coverLetter"
                    value={formData.coverLetter}
                    onChange={handleChange}
                    rows={5}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    placeholder="简单介绍一下自己和为什么适合这个职位..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 bg-primary-600 text-white py-3 rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                      提交中...
                    </>
                  ) : (
                    <>
                      <Send size={18} /> 提交申请
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Resume Preview */}
          <div>
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-24">
              <div className="flex items-center gap-2 mb-4">
                <FileText size={20} className="text-primary-600" />
                <h3 className="font-semibold">简历预览</h3>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-line font-mono">
                {generateResume()}
              </div>
              <p className="text-xs text-gray-500 mt-4">
                * 此简历将随申请一起发送
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ApplyPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    }>
      <ApplyContent />
    </Suspense>
  );
}