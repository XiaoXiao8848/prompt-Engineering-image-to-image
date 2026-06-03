import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { productsApi } from "@/api/products"
import { scenesApi } from "@/api/scenes"
import { jobsApi } from "@/api/jobs"
import {
  Package,
  Image,
  Wand2,
  List,
  ArrowRight,
  Loader2,
} from "lucide-react"

export default function DashboardPage() {
  const navigate = useNavigate()

  const { data: productsData, isLoading: productsLoading } = useQuery({
    queryKey: ["products", { page_size: 1 }],
    queryFn: () => productsApi.list({ page_size: 1 }),
  })

  const { data: scenesData, isLoading: scenesLoading } = useQuery({
    queryKey: ["scenes", { page_size: 1 }],
    queryFn: () => scenesApi.list({ page_size: 1 }),
  })

  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs", { page_size: 5 }],
    queryFn: () => jobsApi.list({ page_size: 5 }),
  })

  const stats = [
    {
      label: "Products",
      value: productsData?.pagination?.total ?? 0,
      icon: Package,
      color: "text-blue-600",
      bg: "bg-blue-50",
      onClick: () => navigate("/products"),
    },
    {
      label: "Scenes",
      value: scenesData?.pagination?.total ?? 0,
      icon: Image,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      onClick: () => navigate("/scenes"),
    },
    {
      label: "Generate",
      value: "New",
      icon: Wand2,
      color: "text-purple-600",
      bg: "bg-purple-50",
      onClick: () => navigate("/generate"),
    },
    {
      label: "Jobs",
      value: jobsData?.pagination?.total ?? 0,
      icon: List,
      color: "text-amber-600",
      bg: "bg-amber-50",
      onClick: () => navigate("/jobs"),
    },
  ]

  const isLoading = productsLoading || scenesLoading || jobsLoading

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your prompt engineering workspace</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => {
              const Icon = stat.icon
              return (
                <button
                  key={stat.label}
                  onClick={stat.onClick}
                  className="bg-white border border-gray-200 rounded-xl p-6 text-left hover:shadow-md transition-shadow"
                >
                  <div className={`w-10 h-10 ${stat.bg} rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
                </button>
              )
            })}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Recent Jobs</h2>
              <button
                onClick={() => navigate("/jobs")}
                className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </button>
            </div>
            {jobsData?.items?.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                No jobs yet. <button onClick={() => navigate("/generate")} className="text-indigo-600 font-medium">Create your first generation</button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {jobsData?.items?.map((job) => (
                  <div
                    key={job.job_uuid}
                    onClick={() => navigate(`/jobs/${job.job_uuid}`)}
                    className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">{job.job_uuid.slice(0, 8)}...</p>
                      <p className="text-xs text-gray-500 mt-0.5 capitalize">{job.mode} mode</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                          job.status === "completed" ? "bg-green-100 text-green-700" :
                          job.status === "failed" ? "bg-red-100 text-red-700" :
                          job.status === "running" ? "bg-blue-100 text-blue-700" :
                          "bg-gray-100 text-gray-700"
                        }`}>
                          {job.status}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {job.completed_tasks}/{job.total_tasks}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
