import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { productsApi } from "@/api/products"
import { scenesApi } from "@/api/scenes"
import { promptsApi } from "@/api/prompts"
import { Wand2, Loader2, Copy, Check, ArrowRight, Image, Package } from "lucide-react"
import { toast } from "sonner"

export default function GenerateSingle() {
  const navigate = useNavigate()
  const [productUuid, setProductUuid] = useState("")
  const [sceneId, setSceneId] = useState("")
  const [mode, setMode] = useState<"template" | "llm">("template")
  const [result, setResult] = useState<any>(null)
  const [copied, setCopied] = useState(false)

  const { data: productsData } = useQuery({
    queryKey: ["products", { page_size: 100 }],
    queryFn: () => productsApi.list({ page_size: 100 }),
  })

  const { data: scenesData } = useQuery({
    queryKey: ["scenes", { page_size: 100 }],
    queryFn: () => scenesApi.list({ page_size: 100 }),
  })

  const generateMutation = useMutation({
    mutationFn: promptsApi.generate,
    onSuccess: (data) => {
      setResult(data)
      toast.success("Generated successfully")
    },
    onError: (err: any) => {
      toast.error(err.message)
    },
  })

  const handleGenerate = () => {
    if (!productUuid || !sceneId) {
      toast.error("Please select a product and scene")
      return
    }
    generateMutation.mutate({ product_uuid: productUuid, scene_id: sceneId, mode })
  }

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Generate Prompt</h1>
        <p className="text-gray-500 mt-1">Create a single prompt for your product</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-6">
        {/* Step 1: Product */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <Package className="w-4 h-4" /> Step 1: Select Product
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

        {/* Step 2: Scene */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <Image className="w-4 h-4" /> Step 2: Select Scene
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {scenesData?.items.map((scene) => (
              <button
                key={scene.scene_id}
                onClick={() => setSceneId(scene.scene_id)}
                className={`p-3 border rounded-lg text-left transition-colors ${
                  sceneId === scene.scene_id
                    ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                <p className="font-medium text-sm text-gray-900">{scene.name}</p>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{scene.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Mode */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-2 block">Step 3: Generation Mode</label>
          <div className="flex gap-3">
            <button
              onClick={() => setMode("template")}
              className={`flex-1 px-4 py-3 border rounded-lg text-sm font-medium transition-colors ${
                mode === "template"
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 text-gray-700 hover:bg-gray-50"
              }`}
            >
              Template Mode
              <p className="text-xs font-normal text-gray-500 mt-1">Fast, deterministic</p>
            </button>
            <button
              onClick={() => setMode("llm")}
              className={`flex-1 px-4 py-3 border rounded-lg text-sm font-medium transition-colors ${
                mode === "llm"
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 text-gray-700 hover:bg-gray-50"
              }`}
            >
              LLM Mode
              <p className="text-xs font-normal text-gray-500 mt-1">Creative, natural</p>
            </button>
          </div>
        </div>

        {/* Generate */}
        <button
          onClick={handleGenerate}
          disabled={generateMutation.isPending || !productUuid || !sceneId}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {generateMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Wand2 className="w-5 h-5" />
          )}
          Generate Prompt
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Result</h2>
            <div className="flex gap-2">
              <button
                onClick={() => handleCopy(result.prompt)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                {copied ? "Copied" : "Copy"}
              </button>
              <button
                onClick={() => navigate("/generate/batch")}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Batch <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Prompt</label>
              <div className="mt-1.5 bg-gray-50 border border-gray-200 rounded-lg p-4 font-mono text-sm text-gray-800 whitespace-pre-wrap">
                {result.prompt}
              </div>
            </div>
            {result.negative_prompt && (
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Negative Prompt</label>
                <div className="mt-1.5 bg-red-50 border border-red-100 rounded-lg p-4 font-mono text-sm text-red-800 whitespace-pre-wrap">
                  {result.negative_prompt}
                </div>
              </div>
            )}
            {result.parameters && Object.keys(result.parameters).length > 0 && (
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Parameters</label>
                <div className="mt-1.5 bg-gray-50 border border-gray-200 rounded-lg p-4 font-mono text-sm text-gray-800">
                  <pre>{JSON.stringify(result.parameters, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
