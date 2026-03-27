<template>
  <div class="p-6 max-w-7xl mx-auto space-y-8 bg-gray-50 dark:bg-gray-950 min-h-screen">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
        Product Performance Report
      </h1>
      <div class="flex flex-wrap gap-3">
        <button
          @click="fetchReport"
          class="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg shadow-md transition transform hover:scale-105 flex items-center gap-2 font-medium"
        >
          Refresh
        </button>
        <button
          @click="exportToExcel"
          class="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg shadow-md transition transform hover:scale-105 flex items-center gap-2 font-medium"
        >
          Export Excel
        </button>
        <button
          @click="exportToPDF"
          class="bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-lg shadow-md transition transform hover:scale-105 flex items-center gap-2 font-medium"
        >
          Export PDF
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-6">
      <div class="grid grid-cols-1 md:grid-cols-5 gap-5">
        <div>
          <label class="block text-sm font-medium  mb-1.5">Search Product</label>
          <input
            v-model="searchQuery"
            @input="debouncedFetch"
            placeholder="Product name..."
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium  mb-1.5">From Date</label>
          <input
            v-model="dateRange.start"
            type="date"
            @change="fetchReport"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium  mb-1.5">To Date</label>
          <input
            v-model="dateRange.end"
            type="date"
            @change="fetchReport"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium  mb-1.5">Quick Range</label>
          <select
            v-model="quickRange"
            @change="applyQuickRange"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          >
            <option value="">Custom</option>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="last-7-days">Last 7 Days</option>
            <option value="last-30-days">Last 30 Days</option>
            <option value="this-month">This Month</option>
            <option value="this-year">This Year</option>
          </select>
        </div>

        <div class="flex items-end">
          <button
            @click="fetchReport"
            class="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg shadow transition transform hover:scale-105 font-medium"
          >
            Apply
          </button>
        </div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Revenue</p>
        <p class="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
          {{ formatCurrency(totalRevenue) }}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Top Product</p>
        <p class="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1 truncate max-w-[240px]">
          {{ topProduct?.product_name || '—' }}
        </p>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ formatCurrency(topProduct?.total_revenue || 0) }}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Product-Unit Combinations</p>
        <p class="text-3xl font-bold text-violet-600 dark:text-violet-400 mt-1">
          {{ filteredData.length }}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Revenue / Sale</p>
        <p class="text-3xl font-bold text-amber-600 dark:text-amber-400 mt-1">
          {{ formatCurrency(averageRevenue) }}
        </p>
      </div>
    </div>

    <!-- Loading / Empty -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="animate-spin rounded-full h-14 w-14 border-4 border-indigo-500 border-t-transparent"></div>
      <p class="mt-6 text-lg text-gray-600 dark:text-gray-400">Loading performance data...</p>
    </div>

    <div v-else-if="!loading && filteredData.length === 0" class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
      <h3 class="text-xl font-semibold  mb-3">No performance data</h3>
      <p class="text-gray-600 dark:text-gray-400">No sales found in the selected period or matching your search.</p>
    </div>

    <!-- Performance Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-900/60 sticky top-0 z-10">
            <tr>
              <th class="p-4 text-center text-xs font-semibold  uppercase tracking-wider w-16">Rank</th>
              <th class="p-4 text-left text-xs font-semibold  uppercase tracking-wider">Product</th>
              <th class="p-4 text-left text-xs font-semibold  uppercase tracking-wider">Unit</th>
              <th class="p-4 text-right text-xs font-semibold  uppercase tracking-wider">Qty Sold</th>
              <th class="p-4 text-right text-xs font-semibold  uppercase tracking-wider">Avg Price</th>
              <th class="p-4 text-right text-xs font-semibold  uppercase tracking-wider">Total Revenue</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="(item, index) in paginatedData" :key="`${item.product_id}-${item.unit_id}`" class="hover:bg-indigo-50/30 dark:hover:bg-gray-800/40 transition text-black dark:text-gray-200">
              <td class="p-4 text-center font-bold ">
                {{ (currentPage - 1) * itemsPerPage + index + 1 }}
              </td>
              <td class="p-4 font-medium ">{{ item.product_name }}</td>
              <td class="p-4 ">{{ item.unit_name || '—' }}</td>
              <td class="p-4 text-right font-medium ">{{ item.quantity_sold || 0 }}</td>
              <td class="p-4 text-right ">{{ formatCurrency(item.avg_price) }}</td>
              <td class="p-4 text-right font-bold text-emerald-700 dark:text-emerald-400">
                {{ formatCurrency(item.total_revenue) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex flex-col sm:flex-row justify-between items-center gap-6 mt-8 text-sm ">
      <div>
        Showing
        <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
        to
        <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredData.length) }}</span>
        of
        <span class="font-medium">{{ filteredData.length }}</span> product-unit sales
      </div>

      <div class="flex items-center gap-4">
        <button
          @click="currentPage--"
          :disabled="currentPage === 1"
          class="px-5 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition font-medium text-black dark:text-gray-200"
        >
          Previous
        </button>

        <span class="font-medium text-black dark:text-gray-200">
          Page {{ currentPage }} / {{ totalPages }}
        </span>

        <button
          @click="currentPage++"
          :disabled="currentPage === totalPages"
          class="px-5 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition font-medium text-black dark:text-gray-200"
        >
          Next
        </button>

        <select
          v-model="itemsPerPage"
          class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-black dark:text-gray-200"
        >
          <option :value="10">10 per page</option>
          <option :value="20">20 per page</option>
          <option :value="50">50 per page</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import debounce from 'lodash.debounce'
import api from '@/api'
import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import 'jspdf-autotable'

const reportData = ref([])
const searchQuery = ref('')
const dateRange = ref({ start: '', end: '' })
const quickRange = ref('')
const currentPage = ref(1)
const itemsPerPage = ref(20)
const loading = ref(false)

const debouncedFetch = debounce(fetchReport, 500)

async function fetchReport() {
  loading.value = true
  currentPage.value = 1

  try {
    const params = {}
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
    if (dateRange.value.start) params.start_date = dateRange.value.start
    if (dateRange.value.end) params.end_date = dateRange.value.end

    const res = await api.get('/reports/performance-list', { params })
    reportData.value = res.data || []
  } catch (err) {
    console.error('Failed to load performance report:', err)
    reportData.value = []
  } finally {
    loading.value = false
  }
}

const formatCurrency = n => n == null ? '0.00' : Number(n).toLocaleString(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})

const filteredData = computed(() => {
  let data = [...reportData.value]
  if (searchQuery.value.trim()) {
    const term = searchQuery.value.toLowerCase()
    data = data.filter(item =>
      item.product_name?.toLowerCase().includes(term) ||
      item.unit_name?.toLowerCase().includes(term)
    )
  }
  return data
})

const totalPages = computed(() => Math.ceil(filteredData.value.length / itemsPerPage.value))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  return filteredData.value.slice(start, start + itemsPerPage.value)
})

const totalRevenue = computed(() =>
  reportData.value.reduce((sum, item) => sum + (Number(item.total_revenue) || 0), 0)
)

const topProduct = computed(() => reportData.value[0] || null)

const averageRevenue = computed(() => {
  const count = reportData.value.length
  return count > 0 ? totalRevenue.value / count : 0
})

function applyQuickRange() {
  const today = new Date()
  let start = ''
  let end = today.toISOString().split('T')[0]

  switch (quickRange.value) {
    case 'today': {
      start = end
      break
    }
    case 'yesterday': {
      const y = new Date(today)
      y.setDate(y.getDate() - 1)
      start = end = y.toISOString().split('T')[0]
      break
    }
    case 'last-7-days': {
      const l7 = new Date(today)
      l7.setDate(l7.getDate() - 7)
      start = l7.toISOString().split('T')[0]
      break
    }
    case 'last-30-days': {
      const l30 = new Date(today)
      l30.setDate(l30.getDate() - 30)
      start = l30.toISOString().split('T')[0]
      break
    }
    case 'this-month': {
      start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
      break
    }
    case 'this-year': {
      start = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0]
      break
    }
  }

  dateRange.value.start = start
  dateRange.value.end = end
  fetchReport()
}

function exportToExcel() {
  const data = reportData.value.map((item, i) => ({
    Rank: i + 1,
    Product: item.product_name,
    Unit: item.unit_name || '—',
    'Qty Sold': item.quantity_sold || 0,
    'Avg Price': Number(item.avg_price || 0).toFixed(2),
    'Total Revenue': Number(item.total_revenue || 0).toFixed(2)
  }))

  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Performance')
  XLSX.writeFile(wb, 'Product_Performance_Report.xlsx')
}

function exportToPDF() {
  const doc = new jsPDF()
  doc.setFontSize(16)
  doc.text('Product Performance Report', 14, 20)

  doc.autoTable({
    head: [['Rank', 'Product', 'Unit', 'Qty Sold', 'Avg Price', 'Total Revenue']],
    body: reportData.value.map((item, i) => [
      i + 1,
      item.product_name,
      item.unit_name || '—',
      item.quantity_sold || 0,
      Number(item.avg_price || 0).toFixed(2),
      Number(item.total_revenue || 0).toFixed(2)
    ]),
    startY: 30,
    styles: { fontSize: 9, cellPadding: 3 },
    headStyles: { fillColor: [79, 70, 229] },
    alternateRowStyles: { fillColor: [243, 244, 246] }
  })

  doc.save('Product_Performance_Report.pdf')
}

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
tr {
  transition: background-color 0.2s ease;
  color: #000000;
}

.dark tr {
  color: #e5e7eb;
}

td, th {
  vertical-align: middle;
}
</style>
