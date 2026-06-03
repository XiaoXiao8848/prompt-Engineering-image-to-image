import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { productsApi } from "@/api/products"
import { scenesApi } from "@/api/scenes"
import { promptsApi } from "@/api/prompts"
import { Wand2, Loader2, Check, ArrowRight, Package, Image } from "lucide-react"
import { toast } from "sonner"

export default function GenerateBatch() {
  const navigate = useNavigate()
  const [productUuid, setProductUuid] = useState("")
  const [selectedScenes, setSelectedScenes] = useState<Set<string>>(new Set())
  const [mode, setMode] = useState<"template" | "llm">("template")
  const [submittedJob, setSubmittedJob] = useState<any>(null)

  const { data: productsData } = useQuery({
    queryKey: ["products", { page_size: 100 }],
    queryFn: () => productsApi.list({ page_size: 100 }),
  })

  const { data: scenesData } = useQuery({
    queryKey: ["scenes", { page_size: 100 }],
    queryFn: () => scenesApi.list({ page_size: 100 }),
  })

  const batchMutation = useMutation({
    mutationFn: promptsApi.generateBatch,
    onSuccess: (data) => {
      setSubmittedJob(data)
      toast.success("Batch job submitted")
    },
    onError: (err: any) => {
      toast.error(err.message)
    },
  })

  const toggleScene = (sceneId: string) => {
    const next = new Set(selectedScenes)
    if (next.has(sceneId)) next.delete(sceneId)
    else next.add(sceneId)
    setSelectedScenes(next)
  }

  const handleSubmit = () => {
    if (!productUuid || selectedScenes.size === 0) {
      toast.error("Please select a product and at least one scene")
      return
    }
    batchMutation.mutate({
      product_uuid: productUuid,
      scene_ids: Array.from(selectedScenes),
      mode,
    })
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Batch Generate</h1>
        <p className="text-gray-500 mt-1">Generate prompts for multiple scenes at once</p>
      </div>

      {!submittedJob ? (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-6">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Package className="w-4 h-4" /> Select Product
            </label>
            <select
              value={productUuid}
              onChange={(e) => setProductUuid(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
            >
              <option value="">Choose a product...</option>
              {productsData?.items.map((p) => (
                <option key={p.product_uuid} value={p.product_uuid}>{p.product_name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Image className="w-4 h-4" /> Select Scenes ({selectedScenes.size} selected)
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {scenesData?.items.map((scene) => {
                const selected = selectedScenes.has(scene.scene_id)
                return (
                  <button
                    key={scene.scene_id}
                    onClick={() => toggleScene(scene.scene_id)}
                    className={`relative p-3 border rounded-lg text-left transition-colors ${
                      selected
                        ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {selected && (
                      <div className="absolute top-2 right-2">
                        <Check className="w-4 h-4 text-indigo-600" />
                      </div>
                    )}
                    <p className="font-medium text-sm text-gray-900 pr-5">{scene.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{scene.description}</p>
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Generation Mode</label>
            <div className="flex gap-3">
              <button onClick={() => setMode("template")}
                className={`flex-1 px-4 py-3 border rounded-lg text-sm font-medium transition-colors ${
                  mode === "template" ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-gray-200 text-gray-700 hover:bg-gray-50"
                }`}>
                Template Mode
                <p className="text-xs font-normal text-gray-500 mt-1">Fast, deterministic</p>
              </button>
              <button onClick={() => setMode("llm")}
                className={`flex-1 px-4 py-3 border rounded-lg text-sm font-medium transition-colors ${
                  mode === "llm" ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-gray-200 text-gray-700 hover:bg-gray-50"
                }`}>
                LLM Mode
                <p className="text-xs font-normal text-gray-500 mt-1">Creative, natural</p>
              </button>
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={batchMutation.isPending || !productUuid || selectedScenes.size === 0}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {batchMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Wand2 className="w-5 h-5" />
            )}
            Submit Batch Job ({selectedScenes.size} scenes)
          </button>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center space-y-4">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Batch Job Submitted</h2>
          <p className="text-gray-500">Your job is being processed in the background</p>
          <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm text-gray-700 max-w-md mx-auto">
            {submittedJob.job_uuid}
          </div>
          <div className="flex justify-center gap-3 pt-2">
            <button
              onClick={() => navigate(`/jobs/${submittedJob.job_uuid}`)}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
            >
              View Progress <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => { setSubmittedJob(null); setSelectedScenes(new Set()) }}
              className="px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              New Batch
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
