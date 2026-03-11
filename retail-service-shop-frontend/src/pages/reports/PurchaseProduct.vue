<template>
  <div class="p-6 max-w-7xl mx-auto space-y-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <h1 class="text-3xl font-bold text-gray-900">Purchase History Report</h1>
      
      <button
        @click="clearFilters"
        class="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition"
      >
        Clear Filters
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            v-model="search"
            placeholder="Product, invoice, supplier..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            @input="debouncedFetch"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">From Date</label>
          <input
            type="date"
            v-model="startDate"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            @change="fetchData"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">To Date</label>
          <input
            type="date"
            v-model="endDate"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            @change="fetchData"
          />
        </div>

        <div class="flex items-end">
          <button
            @click="fetchData"
            class="w-full md:w-auto px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-indigo-500 border-t-transparent"></div>
      <p class="mt-4 text-gray-600">Loading purchase records...</p>
    </div>

    <!-- No Data -->
    <div v-else-if="!loading && reportData.length === 0" class="bg-white p-12 rounded-xl shadow-sm border border-gray-200 text-center">
      <p class="text-gray-500 text-lg">No purchase records found for the selected filters</p>
      <p class="text-sm text-gray-400 mt-2">Try adjusting your search or date range</p>
    </div>

    <!-- Content -->
    <div v-else class="space-y-8">
      <!-- Grand Totals -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p class="text-sm text-gray-600">Total Records</p>
          <p class="text-3xl font-bold text-gray-900 mt-1">{{ formatNumber(localTotalRecords) }}</p>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p class="text-sm text-gray-600">Total Quantity</p>
          <p class="text-3xl font-bold text-indigo-700 mt-1">{{ formatNumber(localTotals.quantity) }}</p>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p class="text-sm text-gray-600">Total Amount</p>
          <p class="text-3xl font-bold text-green-700 mt-1">{{ formatCurrency(localTotals.amount) }}</p>
        </div>
      </div>

      <!-- Table / Grouped View -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PO ID</th>
                <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supplier</th>
                <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th class="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                <th class="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Unit Price</th>
                <th class="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                <th class="px-6 py-4 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <template v-for="(group, index) in groupedData" :key="index">
                <!-- Invoice Group Header -->
                <tr class="bg-indigo-50/40">
                  <td colspan="10" class="px-6 py-4">
                    <div class="flex justify-between items-center">
                      <div>
                        <span class="font-medium text-indigo-800">Invoice: {{ group.invoice_number }}</span>
                        <span class="ml-4 text-sm text-gray-600">• {{ group.date }}</span>
                        <span class="ml-4 text-sm text-gray-600">• {{ group.supplier }}</span>
                      </div>
                      <div class="text-right font-medium">
                        <span class="text-indigo-700">{{ formatCurrency(group.subtotal) }}</span>
                        <span class="text-gray-500 text-sm ml-2">({{ group.items.length }} items)</span>
                      </div>
                    </div>
                  </td>
                </tr>

                <!-- Items -->
                <tr
                  v-for="row in group.items"
                  :key="`${row.purchase_id}-${row.product}-${row.quantity}`"
                  class="hover:bg-gray-50 transition-colors"
                >
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ row.purchase_id }}</td>
                  <td class="px-6 py-4 text-sm text-gray-900">{{ row.product }}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">{{ row.category || '—' }}</td>
                  <td class="px-6 py-4 text-sm text-gray-900">{{ row.supplier }}</td>
                  <td class="px-6 py-4 text-sm text-gray-900">{{ row.invoice_number }}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">{{ formatDate(row.purchase_date) }}</td>
                  <td class="px-6 py-4 text-sm text-right text-gray-900">{{ formatNumber(row.quantity) }}</td>
                  <td class="px-6 py-4 text-sm text-right text-gray-900">{{ formatCurrency(row.unit_price) }}</td>
                  <td class="px-6 py-4 text-sm text-right font-medium text-gray-900">{{ formatCurrency(row.total_price) }}</td>
                  <td class="px-6 py-4 text-center">
                    <router-link
                      :to="`/purchase-orders/${row.purchase_id}/edit`"
                      class="inline-flex items-center px-3 py-1.5 bg-yellow-500 text-white text-sm rounded-md hover:bg-indigo-700 transition"
                      title="Edit"
                    >
                      Edit
                    </router-link>
                
                    <router-link
                      :to="`/purchase-orders/${row.purchase_id}`"
                      class="inline-flex items-center px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 transition"
                    >
                      View PO
                    </router-link>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div class="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white p-5 rounded-xl shadow-sm border border-gray-200">
        <div class="text-sm text-gray-700">
          Showing page <span class="font-medium">{{ page }}</span> of {{ Math.ceil(totalRecords / perPage) || 1 }}
        </div>
        <div class="flex gap-3">
          <button
            @click="prevPage"
            :disabled="page === 1"
            class="px-5 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition"
          >
            Previous
          </button>
          <button
            @click="nextPage"
            :disabled="page >= Math.ceil(totalRecords / perPage)"
            class="px-5 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { debounce } from 'lodash' // ← install lodash or use your own debounce
import api from '@/api'

const reportData = ref([])
const loading = ref(false)
const page = ref(1)
const perPage = 100
const totalRecords = ref(0)

const search = ref('')
const startDate = ref('')
const endDate = ref('')

// Local calculated totals (frontend only)
const localTotals = computed(() => {
  return reportData.value.reduce(
    (acc, row) => ({
      quantity: acc.quantity + (row.quantity || 0),
      amount: acc.amount + (row.total_price || 0)
    }),
    { quantity: 0, amount: 0 }
  )
})

const localTotalRecords = computed(() => reportData.value.length)

// Group data by invoice_number
const groupedData = computed(() => {
  const groups = {}
  reportData.value.forEach(row => {
    const key = row.invoice_number
    if (!groups[key]) {
      groups[key] = {
        invoice_number: row.invoice_number,
        date: formatDate(row.purchase_date),
        supplier: row.supplier,
        items: [],
        subtotal: 0
      }
    }
    groups[key].items.push(row)
    groups[key].subtotal += row.total_price || 0
  })
  return Object.values(groups)
})

/* ──────────────────────────────────────── */
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: perPage,
      search: search.value.trim() || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined
    }

    const res = await api.get('/reports/purchased-product', { params })

    reportData.value = res.data.data || []
    totalRecords.value = Number(res.data.total_records || 0)
  } catch (err) {
    console.error('Report fetch failed:', err)
    reportData.value = []
  } finally {
    loading.value = false
  }
}

const debouncedFetch = debounce(fetchData, 600)

const clearFilters = () => {
  search.value = ''
  startDate.value = ''
  endDate.value = ''
  page.value = 1
  fetchData()
}

const nextPage = () => {
  if (page.value < Math.ceil(totalRecords.value / perPage)) {
    page.value++
    fetchData()
  }
}

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    fetchData()
  }
}

/* Formatters */
const formatDate = d => d ? new Date(d).toLocaleDateString('en-GB', {
  year: 'numeric',
  month: 'short',
  day: 'numeric'
}) : '—'

const formatNumber = n => n == null ? '0' : Number(n).toLocaleString()
const formatCurrency = n => n == null ? '0.00' : Number(n).toLocaleString(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})

watch([search, startDate, endDate], () => {
  page.value = 1
})

onMounted(fetchData)
</script>

<style scoped>
/* You can keep your previous styles or add these for better look */
.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}
</style>