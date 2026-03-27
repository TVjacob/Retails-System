<template>
  <div class="p-6 max-w-7xl mx-auto space-y-8 bg-gray-50 dark:bg-gray-950 min-h-screen">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
        Consumption Report
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
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Search</label>
          <input
            v-model="searchQuery"
            @input="debouncedFetch"
            placeholder="Product name, reason, invoice..."
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">From Date</label>
          <input
            v-model="dateRange.start"
            type="date"
            @change="fetchReport"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">To Date</label>
          <input
            v-model="dateRange.end"
            type="date"
            @change="fetchReport"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Quick Range</label>
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
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Consumption Value</p>
        <p class="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
          {{ formatCurrency(totalConsumptionValue) }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Quantity</p>
        <p class="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
          {{ totalQuantity }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Records</p>
        <p class="text-3xl font-bold text-violet-600 dark:text-violet-400 mt-1">
          {{ filteredData.length }}
        </p>
      </div>
    </div>

    <!-- Loading / Empty -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="animate-spin rounded-full h-14 w-14 border-4 border-indigo-500 border-t-transparent"></div>
      <p class="mt-6 text-lg text-gray-600 dark:text-gray-400">Loading consumption data...</p>
    </div>

    <div v-else-if="!loading && filteredData.length === 0" class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
      <h3 class="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-3">No consumption found</h3>
      <p class="text-gray-600 dark:text-gray-400">Try adjusting the date range or search term.</p>
    </div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-900/60 sticky top-0 z-10">
            <tr>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Date</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Product</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Unit</th>
              <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Qty</th>
              <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Sell Price</th>
              <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Total Value</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Type</th>
              <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider min-w-[240px]">Reason / Invoice</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="item in paginatedData" :key="item.id" class="hover:bg-indigo-50/30 dark:hover:bg-gray-800/40 transition text-black dark:text-gray-200">
              <td class="p-4">{{ item.date }}</td>
              <td class="p-4 font-medium">{{ item.product_name }}</td>
              <td class="p-4">{{ item.unit || 'piece' }}</td>
              <td class="p-4 text-right font-medium">{{ item.quantity }}</td>
              <td class="p-4 text-right">{{ formatCurrency(item.selling_price) }}</td>
              <td class="p-4 text-right font-semibold text-emerald-700 dark:text-emerald-400">
                {{ formatCurrency(item.total_amount) }}
              </td>
              <td class="p-4">
                <span class="inline-flex px-3 py-1 rounded-full text-xs font-medium"
                      :class="item.type === 'Sale'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'">
                  {{ item.type }}
                </span>
              </td>
              <td class="p-4 text-gray-700 dark:text-gray-300 text-sm">{{ item.reason || '—' }}</td>
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
        <span class="font-medium">{{ filteredData.length }}</span> records
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

    const res = await api.get('/reports/consumption', { params })
    reportData.value = res.data || []
  } catch (err) {
    console.error('Failed to load consumption report:', err)
  } finally {
    loading.value = false
  }
}
// const formatNumber = n => n == null ? '0' : Number(n).toLocaleString()
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
      item.reason?.toLowerCase().includes(term) ||
      item.type?.toLowerCase().includes(term)
    )
  }
  return data
})

const totalPages = computed(() => Math.ceil(filteredData.value.length / itemsPerPage.value))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  return filteredData.value.slice(start, start + itemsPerPage.value)
})

const totalConsumptionValue = computed(() =>
  reportData.value.reduce((sum, item) => sum + (Number(item.total_amount) || 0), 0)
)

const totalQuantity = computed(() =>
  reportData.value.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0)
)

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
  }

  dateRange.value.start = start
  dateRange.value.end = end
  fetchReport()
}

function exportToExcel() {
  const data = reportData.value.map((item, i) => ({
    '#': i + 1,
    Date: item.date,
    Product: item.product_name,
    Unit: item.unit || 'piece',
    Quantity: item.quantity,
    'Selling Price': item.selling_price || 0,
    'Total Amount': item.total_amount || 0,
    Type: item.type,
    'Reason / Invoice': item.reason || ''
  }))

  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Consumption')
  XLSX.writeFile(wb, 'Consumption_Report.xlsx')
}

function exportToPDF() {
  const doc = new jsPDF()
  doc.setFontSize(16)
  doc.text('Consumption Report', 14, 20)

  doc.autoTable({
    head: [['Date', 'Product', 'Unit', 'Qty', 'Sell Price', 'Total Amount', 'Type', 'Reason']],
    body: reportData.value.map(item => [
      item.date,
      item.product_name,
      item.unit || 'piece',
      item.quantity,
      item.selling_price || 0,
      item.total_amount || 0,
      item.type,
      item.reason || ''
    ]),
    startY: 30,
    styles: { fontSize: 9, cellPadding: 3 },
    headStyles: { fillColor: [79, 70, 229] },
    alternateRowStyles: { fillColor: [243, 244, 246] },
    columnStyles: { 7: { cellWidth: 50 } }
  })

  doc.save('Consumption_Report.pdf')
}

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
/* Black text in light mode, light in dark */
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
