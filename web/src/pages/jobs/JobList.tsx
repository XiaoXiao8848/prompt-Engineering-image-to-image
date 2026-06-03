import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { jobsApi } from "@/api/jobs"
import { List, Loader2, ArrowRight } from "lucide-react"

export default function JobList() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", { page, status }],
    queryFn: () => jobsApi.list({ page, status: status || undefined }),
    refetchInterval: 5000,
  })

  const statusOptions = ["", "pending", "queued", "running", "completed", "failed", "partial"]

  const getStatusColor = (s: string) => {
    switch (s) {
      case "completed": return "bg-green-100 text-green-700"
      case "failed": return "bg-red-100 text-red-700"
      case "running": return "bg-blue-100 text-blue-700"
      case "queued": return "bg-purple-100 text-purple-700"
      case "partial": return "bg-amber-100 text-amber-700"
      default: return "bg-gray-100 text-gray-700"
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <p className="text-gray-500 mt-1">Monitor your generation jobs</p>
      </div>

      <div className="flex gap-3">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white text-sm"
        >
          {statusOptions.map((s) => (
            <option key={s} value={s}>{s ? s.charAt(0).toUpperCase() + s.slice(1) : "All Statuses"}</option>
          ))}
        </select>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
          </div>
        ) : data?.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-500">
            <List className="w-10 h-10 mb-3 text-gray-300" />
            <p>No jobs found</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Job ID</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Mode</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Status</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Progress</th>
                <th className="px-6 py-3 text-right font-medium text-gray-700"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((job) => (
                <tr
                  key={job.job_uuid}
                  onClick={() => navigate(`/jobs/${job.job_uuid}`)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4 font-mono text-xs text-gray-600">{job.job_uuid.slice(0, 12)}...</td>
                  <td className="px-6 py-4 text-gray-600 capitalize">{job.mode}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 rounded-full transition-all"
                          style={{
                            width: `${job.total_tasks > 0 ? (job.completed_tasks / job.total_tasks) * 100 : 0}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">
                        {job.completed_tasks}/{job.total_tasks}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <ArrowRight className="w-4 h-4 text-gray-400 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Previous</button>
          <span className="text-sm text-gray-600">Page {page} of {data.pagination.total_pages}</span>
          <button onClick={() => setPage(p => Math.min(data.pagination.total_pages, p + 1))} disabled={!data.pagination.has_next}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50">Next</button>
        </div>
      )}
    </div>
  )
}
