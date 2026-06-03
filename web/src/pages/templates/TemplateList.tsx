import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { templatesApi } from "@/api/templates"
import { FileText, Search, Loader2, Play, X } from "lucide-react"
import { toast } from "sonner"

export default function TemplateList() {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState("")
  const [renderModal, setRenderModal] = useState<string | null>(null)
  const [renderVars, setRenderVars] = useState("")
  const [renderResult, setRenderResult] = useState<string | null>(null)
  const [rendering, setRendering] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ["templates", { page }],
    queryFn: () => templatesApi.list({ page }),
  })

  const handleRender = async () => {
    if (!renderModal) return
    setRendering(true)
    try {
      const variables: Record<string, string> = {}
      renderVars.split("\n").forEach(line => {
        const [k, v] = line.split("=")
        if (k && v) variables[k.trim()] = v.trim()
      })
      const result = await templatesApi.render(renderModal, variables)
      setRenderResult(result)
    } catch (err: any) {
      toast.error(err.message)
    } finally {
      setRendering(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Templates</h1>
        <p className="text-gray-500 mt-1">Manage prompt templates</p>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search templates..."
          value={keyword}
          onChange={(e) => { setKeyword(e.target.value); setPage(1) }}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
          </div>
        ) : data?.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-500">
            <FileText className="w-10 h-10 mb-3 text-gray-300" />
            <p>No templates found</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Name</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Type</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Default</th>
                <th className="px-6 py-3 text-right font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{t.name}</td>
                  <td className="px-6 py-4 text-gray-600 capitalize">{t.template_type}</td>
                  <td className="px-6 py-4">
                    {t.is_default ? (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">Yes</span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => { setRenderModal(t.template_uuid); setRenderResult(null); setRenderVars("") }}
                      className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    >
                      <Play className="w-4 h-4" />
                    </button>
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

      {renderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Test Render</h2>
              <button onClick={() => setRenderModal(null)} className="text-gray-500 hover:text-gray-700"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Variables (key=value per line)</label>
                <textarea
                  value={renderVars}
                  onChange={(e) => setRenderVars(e.target.value)}
                  rows={4}
                  placeholder="product_name=Serum&#10;brand=LuxBeauty"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                />
              </div>
              <button onClick={handleRender} disabled={rendering}
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50">
                {rendering ? <Loader2 className="w-4 h-4 animate-spin" /> : "Render"}
              </button>
              {renderResult !== null && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1">Result:</p>
                  <p className="text-sm text-gray-900 font-mono whitespace-pre-wrap">{renderResult}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
