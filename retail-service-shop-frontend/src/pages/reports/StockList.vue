<template>
  <div class="p-6 max-w-7xl mx-auto space-y-8 bg-gray-50 dark:bg-gray-950 min-h-screen">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
        Stock List Report
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
        <button
          @click="$router.push('/reports')"
          class="bg-gray-600 hover:bg-gray-700 text-white px-5 py-2.5 rounded-lg shadow-md transition transform hover:scale-105 flex items-center gap-2 font-medium"
        >
          Back to Reports
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div>
          <label class="block text-sm font-medium  mb-1.5">Search</label>
          <input
            v-model="searchQuery"
            @input="debouncedFetch"
            placeholder="Product name, SKU, category..."
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
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
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium ">Total Products</p>
        <p class="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
          {{ filteredData.length }}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium ">Total Stock Value</p>
        <p class="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
          {{ formatCurrency(totalStockValue) }}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium ">Low Stock Items</p>
        <p class="text-3xl font-bold text-rose-600 dark:text-rose-400 mt-1">
          {{ lowStockCount }}
        </p>
      </div>
    </div>

    <!-- Loading / Empty -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="animate-spin rounded-full h-14 w-14 border-4 border-indigo-500 border-t-transparent"></div>
      <p class="mt-6 text-lg ">Loading stock data...</p>
    </div>

    <div v-else-if="!loading && filteredData.length === 0" class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
      <h3 class="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-3">No stock data found</h3>
      <p class="">Try adjusting your search term.</p>
    </div>

    <!-- Stock Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-900/60 sticky top-0 z-10">
            <tr>
              <th class="p-4 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider w-16">#</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Product</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">SKU</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Category</th>
              <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Current Stock</th>
              <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Avg Retail Price</th>
              <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Est. Value</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="(item, index) in paginatedData" :key="item.id" class="hover:bg-indigo-50/30 dark:hover:bg-gray-800/40 transition text-black dark:text-gray-200">
              <td class="p-4 text-center font-medium ">
                {{ (currentPage - 1) * itemsPerPage + index + 1 }}
              </td>
              <td class="p-4 font-medium ">{{ item.name }}</td>
              <td class="p-4 ">{{ item.sku || '—' }}</td>
              <td class="p-4 ">{{ item.category_name || '—' }}</td>
              <td class="p-4 text-right font-medium ">
                {{ item.quantity }}
                <span v-if="item.quantity <= 10" class="ml-2 inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200">
                  Low
                </span>
              </td>
              <td class="p-4 text-right ">{{ formatCurrency(item.avg_retail_price_base) }}</td>
              <td class="p-4 text-right font-semibold text-emerald-700 dark:text-emerald-400">
                {{ formatCurrency(item.estimated_value) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex flex-col sm:flex-row justify-between items-center gap-6 mt-8 text-sm text-gray-700 dark:text-gray-300">
      <div>
        Showing
        <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
        to
        <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredData.length) }}</span>
        of
        <span class="font-medium">{{ filteredData.length }}</span> products
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

    const res = await api.get('/reports/stock-list', { params })
    reportData.value = res.data || []
  } catch (err) {
    console.error('Failed to load stock report:', err)
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
      item.name?.toLowerCase().includes(term) ||
      item.sku?.toLowerCase().includes(term) ||
      item.category_name?.toLowerCase().includes(term)
    )
  }
  return data
})

const totalPages = computed(() => Math.ceil(filteredData.value.length / itemsPerPage.value))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  return filteredData.value.slice(start, start + itemsPerPage.value)
})

const totalStockValue = computed(() =>
  reportData.value.reduce((sum, item) => sum + Number(item.estimated_value || 0), 0)
)

const lowStockCount = computed(() =>
  reportData.value.filter(item => Number(item.quantity) <= 10).length
)

function exportToExcel() {
  const data = reportData.value.map((item, i) => ({
    '#': i + 1,
    Product: item.name,
    SKU: item.sku || '—',
    Category: item.category_name || '—',
    'Current Stock': item.quantity || 0,
    'Avg Retail Price (base)': Number(item.avg_retail_price_base || 0).toFixed(2),
    'Estimated Value': Number(item.estimated_value || 0).toFixed(2)
  }))

  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Stock List')
  XLSX.writeFile(wb, 'Stock_List_Report.xlsx')
}

function exportToPDF() {
  const doc = new jsPDF()
  doc.setFontSize(16)
  doc.text('Stock List Report', 14, 20)

  doc.autoTable({
    head: [['#', 'Product', 'SKU', 'Category', 'Stock', 'Avg Price (base)', 'Est. Value']],
    body: reportData.value.map((item, i) => [
      i + 1,
      item.name,
      item.sku || '—',
      item.category_name || '—',
      item.quantity || 0,
      Number(item.avg_retail_price_base || 0).toFixed(2),
      Number(item.estimated_value || 0).toFixed(2)
    ]),
    startY: 30,
    styles: { fontSize: 9, cellPadding: 3 },
    headStyles: { fillColor: [79, 70, 229] },
    alternateRowStyles: { fillColor: [243, 244, 246] }
  })

  doc.save('Stock_List_Report.pdf')
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
