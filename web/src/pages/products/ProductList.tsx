import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { productsApi } from "@/api/products"
import { Package, Plus, Search, Loader2, Pencil, Trash2 } from "lucide-react"
import { toast } from "sonner"
import type { Product } from "@/types/api"

export default function ProductList() {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["products", { page, keyword }],
    queryFn: () => productsApi.list({ page, keyword: keyword || undefined }),
  })

  const handleDelete = async (uuid: string) => {
    if (!confirm("Delete this product?")) return
    try {
      await productsApi.delete(uuid)
      toast.success("Deleted")
      refetch()
    } catch (err: any) {
      toast.error(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-500 mt-1">Manage your product configurations</p>
        </div>
        <button
          onClick={() => { setEditing(null); setShowForm(true) }}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> New Product
        </button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); setPage(1) }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
          </div>
        ) : data?.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-500">
            <Package className="w-10 h-10 mb-3 text-gray-300" />
            <p>No products found</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Name</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Brand</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Material</th>
                <th className="px-6 py-3 text-left font-medium text-gray-700">Status</th>
                <th className="px-6 py-3 text-right font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{product.product_name}</td>
                  <td className="px-6 py-4 text-gray-600">{product.brand || "—"}</td>
                  <td className="px-6 py-4 text-gray-600">{product.material || "—"}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                      product.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                    }`}>
                      {product.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => { setEditing(product); setShowForm(true) }}
                      className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors mr-1"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(product.product_uuid)}
                      className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
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
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {data.pagination.total_pages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(data.pagination.total_pages, p + 1))}
            disabled={!data.pagination.has_next}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}

      {showForm && (
        <ProductFormModal
          product={editing}
          onClose={() => setShowForm(false)}
          onSuccess={() => { refetch(); setShowForm(false) }}
        />
      )}
    </div>
  )
}

function ProductFormModal({ product, onClose, onSuccess }: {
  product: Product | null
  onClose: () => void
  onSuccess: () => void
}) {
  const [form, setForm] = useState({
    product_id: product?.product_id || "",
    product_name: product?.product_name || "",
    brand: product?.brand || "",
    material: product?.material || "",
    shape: product?.shape || "",
    color: product?.color || "",
    size: product?.size || "",
    lock_tags: product?.lock_tags || "",
    selling_points: product?.selling_points?.join(", ") || "",
    material_keywords: product?.material_keywords?.join(", ") || "",
    brand_tone: product?.brand_tone || "",
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        selling_points: form.selling_points.split(",").map(s => s.trim()).filter(Boolean),
        material_keywords: form.material_keywords.split(",").map(s => s.trim()).filter(Boolean),
      }
      if (product) {
        await productsApi.update(product.product_uuid, payload)
      } else {
        await productsApi.create(payload as any)
      }
      toast.success(product ? "Updated" : "Created")
      onSuccess()
    } catch (err: any) {
      toast.error(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{product ? "Edit Product" : "New Product"}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Product ID</label>
              <input required value={form.product_id} onChange={e => setForm({ ...form, product_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input required value={form.product_name} onChange={e => setForm({ ...form, product_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
              <input value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Material</label>
              <input value={form.material} onChange={e => setForm({ ...form, material: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Shape</label>
              <input value={form.shape} onChange={e => setForm({ ...form, shape: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
              <input value={form.color} onChange={e => setForm({ ...form, color: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lock Tags *</label>
            <textarea required value={form.lock_tags} onChange={e => setForm({ ...form, lock_tags: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            <p className="text-xs text-gray-500 mt-1">Tags that lock the product appearance in generated prompts</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Selling Points (comma separated)</label>
            <input value={form.selling_points} onChange={e => setForm({ ...form, selling_points: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Material Keywords (comma separated)</label>
            <input value={form.material_keywords} onChange={e => setForm({ ...form, material_keywords: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={saving} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
              {saving ? "Saving..." : (product ? "Update" : "Create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
