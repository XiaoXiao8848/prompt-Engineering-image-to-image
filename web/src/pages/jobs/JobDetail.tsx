import { useState, useEffect, useRef } from "react"
import { useQuery } from "@tanstack/react-query"
import { useParams, useNavigate } from "react-router-dom"
import { jobsApi } from "@/api/jobs"
import { Loader2, Copy, Check, ArrowLeft } from "lucide-react"

export default function JobDetail() {
  const { jobUuid } = useParams()
  const navigate = useNavigate()
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [sseProgress, setSseProgress] = useState<any>(null)
  const [sseConnected, setSseConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const { data: detail } = useQuery({
    queryKey: ["job", jobUuid],
    queryFn: () => jobsApi.getDetail(jobUuid!),
    enabled: !!jobUuid,
    refetchInterval: sseConnected ? false : 3000,
  })

  const { data: progress } = useQuery({
    queryKey: ["job-progress", jobUuid],
    queryFn: () => jobsApi.getProgress(jobUuid!),
    enabled: !!jobUuid,
    refetchInterval: sseConnected ? false : 3000,
  })

  const { data: results } = useQuery({
    queryKey: ["job-results", jobUuid],
    queryFn: () => jobsApi.getResults(jobUuid!),
    enabled: !!jobUuid,
    refetchInterval: sseConnected ? false : 3000,
  })

  // SSE connection
  useEffect(() => {
    if (!jobUuid) return
    const token = localStorage.getItem("access_token")
    const es = new EventSource(`/api/v1/jobs/${jobUuid}/stream?token=${token}`)
    eventSourceRef.current = es

    es.addEventListener("progress", (e) => {
      try {
        const data = JSON.parse(e.data)
        setSseProgress(data)
        setSseConnected(true)
      } catch {
        /* ignore parse error */
      }
    })

    es.addEventListener("done", (e) => {
      try {
        const data = JSON.parse(e.data)
        setSseProgress((prev: any) => ({ ...prev, status: data.status }))
        es.close()
      } catch {
        /* ignore */
      }
    })

    es.addEventListener("error", () => {
      setSseConnected(false)
      es.close()
    })

    return () => {
      es.close()
    }
  }, [jobUuid])

  const activeProgress = sseProgress || progress

  const handleCopy = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const getStatusColor = (s: string) => {
    switch (s) {
      case "success": return "bg-green-100 text-green-700"
      case "failed": return "bg-red-100 text-red-700"
      case "running": return "bg-blue-100 text-blue-700"
      case "pending": return "bg-gray-100 text-gray-700"
      default: return "bg-gray-100 text-gray-700"
    }
  }

  if (!detail || !activeProgress) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button
        onClick={() => navigate("/jobs")}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Jobs
      </button>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Job Detail</h1>
        <p className="font-mono text-sm text-gray-500 mt-1">{jobUuid}</p>
      </div>

      {/* Progress Card */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium capitalize ${getStatusColor(activeProgress.status)}`}>
            {activeProgress.status}
          </span>
          <span className="text-2xl font-bold text-gray-900">{activeProgress.progress_percent}%</span>
        </div>

        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-600 rounded-full transition-all duration-500"
            style={{ width: `${activeProgress.progress_percent}%` }}
          />
        </div>

        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-lg font-semibold text-gray-900">{activeProgress.total_tasks}</p>
            <p className="text-xs text-gray-500">Total</p>
          </div>
          <div className="bg-green-50 rounded-lg p-3">
            <p className="text-lg font-semibold text-green-700">{activeProgress.completed_tasks}</p>
            <p className="text-xs text-gray-500">Completed</p>
          </div>
          <div className="bg-red-50 rounded-lg p-3">
            <p className="text-lg font-semibold text-red-700">{activeProgress.failed_tasks}</p>
            <p className="text-xs text-gray-500">Failed</p>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Results</h2>
        </div>

        {!results || results.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            {activeProgress.status === "pending" || activeProgress.status === "queued"
              ? "Waiting to start..."
              : "No results yet"}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {results.map((result) => (
              <div key={result.result_uuid} className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(result.status)}`}>
                    {result.status}
                  </span>
                  {result.prompt && (
                    <button
                      onClick={() => handleCopy(result.prompt!, result.result_uuid)}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {copiedId === result.result_uuid ? (
                        <Check className="w-3.5 h-3.5 text-green-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                      {copiedId === result.result_uuid ? "Copied" : "Copy"}
                    </button>
                  )}
                </div>

                {result.prompt ? (
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-medium text-gray-500 uppercase">Prompt</label>
                      <div className="mt-1 bg-gray-50 border border-gray-200 rounded-lg p-3 font-mono text-sm text-gray-800 whitespace-pre-wrap">
                        {result.prompt}
                      </div>
                    </div>
                    {result.negative_prompt && (
                      <div>
                        <label className="text-xs font-medium text-gray-500 uppercase">Negative</label>
                        <div className="mt-1 bg-red-50 border border-red-100 rounded-lg p-3 font-mono text-sm text-red-800">
                          {result.negative_prompt}
                        </div>
                      </div>
                    )}
                  </div>
                ) : result.error_message ? (
                  <div className="bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-700">
                    {result.error_message}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
