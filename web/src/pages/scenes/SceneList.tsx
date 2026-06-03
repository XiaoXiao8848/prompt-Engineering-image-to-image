import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { scenesApi } from "@/api/scenes"
import { Image, Search, Loader2, Sun, Home, Gem, Droplets, TreePine } from "lucide-react"

const sceneIcons: Record<string, React.ReactNode> = {
  studio_clean: <Sun className="w-6 h-6" />,
  lifestyle_home: <Home className="w-6 h-6" />,
  luxury_marble: <Gem className="w-6 h-6" />,
  water_splash: <Droplets className="w-6 h-6" />,
  outdoor_nature: <TreePine className="w-6 h-6" />,
}

export default function SceneList() {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["scenes", { page, keyword }],
    queryFn: () => scenesApi.list({ page, keyword: keyword || undefined }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Scenes</h1>
        <p className="text-gray-500 mt-1">Browse available generation scenes</p>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search scenes..."
          value={keyword}
          onChange={(e) => { setKeyword(e.target.value); setPage(1) }}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 text-gray-500">
          <Image className="w-10 h-10 mb-3 text-gray-300" />
          <p>No scenes found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((scene) => (
            <div key={scene.id} className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center text-indigo-600 shrink-0">
                  {sceneIcons[scene.scene_id] || <Image className="w-6 h-6" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{scene.name}</h3>
                    {scene.is_builtin && (
                      <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">Built-in</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">{scene.description || "No description"}</p>
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {scene.lighting && (
                      <span className="px-2 py-0.5 bg-amber-50 text-amber-700 text-xs rounded-full">{scene.lighting}</span>
                    )}
                    {scene.background && (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">{scene.background}</span>
                    )}
                    {scene.atmosphere && (
                      <span className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded-full">{scene.atmosphere}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {data && data.pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50"
          >Previous</button>
          <span className="text-sm text-gray-600">Page {page} of {data.pagination.total_pages}</span>
          <button
            onClick={() => setPage(p => Math.min(data.pagination.total_pages, p + 1))}
            disabled={!data.pagination.has_next}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50"
          >Next</button>
        </div>
      )}
    </div>
  )
}
