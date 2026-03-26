"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { MapPin, Briefcase, Heart, Calendar, ArrowLeft, Send } from "lucide-react";

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

interface Comment {
  id: number;
  job_id: number;
  content: string;
  author: string;
  created_at: string;
}

export default function JobDetail() {
  const params = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [liked, setLiked] = useState(false);

  useEffect(() => {
    fetchJobDetails();
    fetchComments();
  }, [params.id]);

  const fetchJobDetails = async () => {
    try {
      const res = await fetch(`/api/jobs/${params.id}`);
      if (res.ok) {
        const data = await res.json();
        setJob(data);
      }
    } catch (error) {
      console.error("Failed to fetch job:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async () => {
    try {
      const res = await fetch(`/api/comments?job_id=${params.id}`);
      if (res.ok) {
        const data = await res.json();
        setComments(data);
      }
    } catch (error) {
      console.error("Failed to fetch comments:", error);
    }
  };

  const handleLike = async () => {
    if (!job) return;
    try {
      await fetch(`/api/jobs/${job.id}/like`, { method: "POST" });
      setJob({ ...job, likes: job.likes + 1 });
      setLiked(true);
    } catch (error) {
      console.error("Failed to like job:", error);
    }
  };

  const handleComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !authorName.trim()) return;

    try {
      const res = await fetch("/api/comments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: Number(params.id),
          content: newComment,
          author: authorName,
        }),
      });

      if (res.ok) {
        const comment = await res.json();
        setComments([comment, ...comments]);
        setNewComment("");
      }
    } catch (error) {
      console.error("Failed to post comment:", error);
    }
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
          <p className="text-gray-500 mb-4">职位不存在</p>
          <a href="/" className="text-primary-600 hover:underline">返回首页</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container py-8">
        <a href="/" className="inline-flex items-center gap-2 text-gray-600 hover:text-primary-600 mb-6">
          <ArrowLeft size={20} /> 返回职位列表
        </a>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Job Info */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{job.title}</h1>
              <p className="text-xl text-gray-600 mb-4">{job.company}</p>

              <div className="flex flex-wrap gap-4 text-gray-600 mb-6">
                <span className="flex items-center gap-2">
                  <MapPin size={18} /> {job.location}, {job.country}
                </span>
                <span className="flex items-center gap-2">
                  <Briefcase size={18} /> {job.category}
                </span>
                {job.salary_range && (
                  <span className="text-green-600 font-medium">{job.salary_range}</span>
                )}
              </div>

              <div className="prose max-w-none">
                <h3 className="font-semibold text-gray-900 mb-2">职位描述</h3>
                <p className="whitespace-pre-line text-gray-700">{job.description}</p>
              </div>

              <div className="mt-6 flex items-center gap-4">
                <button
                  onClick={handleLike}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                    liked
                      ? "bg-red-50 text-red-500"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  <Heart size={20} fill={liked ? "currentColor" : "none"} />
                  {liked ? "已点赞" : "点赞"} ({job.likes})
                </button>
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 text-center bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition"
                >
                  申请职位 →
                </a>
              </div>
            </div>

            {/* Comments */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">评论 ({comments.length})</h2>

              {/* Comment Form */}
              <form onSubmit={handleComment} className="mb-6 p-4 bg-gray-50 rounded-lg">
                <input
                  type="text"
                  placeholder="你的名字"
                  className="w-full px-3 py-2 border rounded mb-3"
                  value={authorName}
                  onChange={(e) => setAuthorName(e.target.value)}
                />
                <textarea
                  placeholder="写下你的评论..."
                  className="w-full px-3 py-2 border rounded mb-3"
                  rows={3}
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                />
                <button
                  type="submit"
                  className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                >
                  <Send size={16} /> 发表评论
                </button>
              </form>

              {/* Comment List */}
              <div className="space-y-4">
                {comments.map((comment) => (
                  <div key={comment.id} className="border-b pb-4 last:border-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">{comment.author}</span>
                      <span className="text-gray-400 text-sm">
                        {new Date(comment.created_at).toLocaleDateString("zh-CN")}
                      </span>
                    </div>
                    <p className="text-gray-700">{comment.content}</p>
                  </div>
                ))}
                {comments.length === 0 && (
                  <p className="text-gray-500 text-center py-4">暂无评论，快来评论吧！</p>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="font-semibold mb-4">职位信息</h3>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">来源</dt>
                  <dd className="font-medium">{job.source}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">发布日期</dt>
                  <dd className="font-medium flex items-center gap-1">
                    <Calendar size={14} />
                    {new Date(job.created_at).toLocaleDateString("zh-CN")}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">点赞数</dt>
                  <dd className="font-medium">{job.likes}</dd>
                </div>
              </dl>
            </div>

            {/* Ad Space */}
            <div className="bg-white rounded-lg p-6 text-center border-2 border-dashed border-gray-300">
              <p className="text-gray-400">侧边栏广告位</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}