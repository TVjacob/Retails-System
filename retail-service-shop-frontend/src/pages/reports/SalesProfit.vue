<template>
  <div class="p-6 max-w-7xl mx-auto space-y-8 bg-gray-50 dark:bg-gray-950 min-h-screen">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
        Sales Profit Report
      </h1>
      <button
        @click="fetchData"
        class="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg shadow-md transition transform hover:scale-105 flex items-center gap-2 font-medium"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-6">
      <div class="grid grid-cols-1 md:grid-cols-5 gap-5">
        <div>
          <label class="block text-sm font-medium text-black  mb-1.5">Search</label>
          <input
            v-model="search"
            @input="debouncedFetchData"
            placeholder="Invoice #, product, customer..."
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-black  mb-1.5">From</label>
          <input
            type="date"
            v-model="startDate"
            @change="fetchData"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-black  mb-1.5">To</label>
          <input
            type="date"
            v-model="endDate"
            @change="fetchData"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-black  mb-1.5">Quick Range</label>
          <select
            v-model="quickRange"
            @change="applyQuickRange"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          >
            <option value="">Custom</option>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="this-week">This Week</option>
            <option value="last-7-days">Last 7 Days</option>
            <option value="this-month">This Month</option>
            <option value="last-30-days">Last 30 Days</option>
          </select>
        </div>

        <div class="flex items-end">
          <button
            @click="fetchData"
            class="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg shadow transition transform hover:scale-105 font-medium"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- Loading / Empty -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="animate-spin rounded-full h-14 w-14 border-4 border-indigo-500 border-t-transparent"></div>
      <p class="mt-6 text-lg text-gray-600 dark:text-gray-400">Loading sales data...</p>
    </div>

    <div v-else-if="!loading && groupedData.length === 0" class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
      <h3 class="text-xl font-semibold text-black  mb-3">No sales found</h3>
      <p class="text-gray-600 dark:text-gray-400">Try adjusting the date range or search term.</p>
    </div>

    <!-- Summary Cards -->
    <!-- Summary Cards – Expanded -->
<div v-else-if="!loading" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
  <!-- Invoices -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Invoices</p>
    <p class="text-3xl md:text-4xl font-bold text-indigo-600 dark:text-indigo-400 mt-2">
      {{ groupedData.length }}
    </p>
  </div>

  <!-- Total Sales -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Sales</p>
    <p class="text-3xl md:text-4xl font-bold text-blue-600 dark:text-blue-400 mt-2">
      {{ formatNumber(summary.total_sales) }}
    </p>
  </div>

  <!-- Credit Sales -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Credit Sales</p>
    <p class="text-3xl md:text-4xl font-bold text-purple-600 dark:text-purple-400 mt-2">
      {{ formatNumber(summary.total_credit_sales) }}
    </p>
  </div>

  <!-- Outstanding Balance -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Outstanding</p>
    <p class="text-3xl md:text-4xl font-bold text-amber-600 dark:text-amber-400 mt-2">
      {{ formatNumber(summary.outstanding_balance) }}
    </p>
  </div>

  <!-- Cash Received -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Cash Received</p>
    <p class="text-3xl md:text-4xl font-bold text-emerald-700 dark:text-emerald-400 mt-2">
      {{ formatNumber(summary.total_cash_received) }}
    </p>
  </div>

  <!-- COGS -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">COGS</p>
    <p class="text-3xl md:text-4xl font-bold text-red-600 dark:text-red-400 mt-2">
      {{ formatNumber(summary.total_cogs) }}
    </p>
  </div>

  <!-- Gross Profit -->
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow border p-5 text-center transition-transform hover:scale-[1.02]">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Gross Profit</p>
    <p
      class="text-3xl md:text-4xl font-bold mt-2"
      :class="summary.gross_profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'"
    >
      {{ formatNumber(summary.gross_profit) }}
    </p>
  </div>

  <!-- Expenses + Net Profit – full width on small, 2 columns on md+ -->
  <div class="md:col-span-2 bg-gradient-to-br from-gray-50 to-white dark:from-gray-800 dark:to-gray-900 rounded-xl shadow border p-6 text-center transition-transform hover:scale-[1.02]">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <div>
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Expenses</p>
        <p class="text-3xl md:text-4xl font-bold text-violet-600 dark:text-violet-400 mt-2">
          {{ formatNumber(summary.total_expenses) }}
        </p>
      </div>
      <div>
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Net Profit</p>
        <p
          class="text-3xl md:text-4xl font-bold mt-2 font-extrabold"
          :class="summary.net_profit >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-700 dark:text-red-300'"
        >
          {{ formatNumber(summary.net_profit) }}
        </p>
      </div>
    </div>
  </div>
</div>

    <!-- Invoice Groups -->
    <div v-if="!loading && groupedData.length > 0" class="space-y-8">
      <div
        v-for="invoice in paginatedGroupedData"
        :key="invoice.invoice"
        class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <!-- Invoice Header -->
        <div class="p-5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 class="text-xl font-bold ">
              {{ invoice.invoice }}
            </h2>
            <p class="text-sm  mt-1">
              {{ invoice.date }} • {{ invoice.customer }}
            </p>
          </div>

          <div class="text-left md:text-right flex flex-col gap-1">
            <p class="text-sm">
              Sales: <span class="font-semibold text-blue-600 dark:text-blue-400">{{ formatNumber(invoice.sales_total) }}</span>
            </p>
            <p class="text-sm">
              Cost: <span class="font-semibold text-red-600 dark:text-red-400">{{ formatNumber(invoice.cost_total) }}</span>
            </p>
            <p class="text-sm">
              Profit:
              <span
                class="font-bold"
                :class="invoice.profit_total >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'"
              >
                {{ formatNumber(invoice.profit_total) }}
              </span>
            </p>
          </div>

          <router-link
            :to="`/editsales/${invoice.sale_id}`"
            class="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg font-medium transition transform hover:scale-105 flex items-center gap-2 shadow-sm"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit Sale
          </router-link>
        </div>

        <!-- Items Table -->
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th class="p-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Product</th>
                <th class="p-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Unit</th>
                <th class="p-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Category</th>
                <th class="p-4 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Qty</th>
                <th class="p-4 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Sell Price</th>
                <th class="p-4 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Buy Price</th>
                <th class="p-4 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Line Sales</th>
                <th class="p-4 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Line Cost</th>
                <th class="p-4 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Profit</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="item in invoice.items" :key="item.sale_id + '-' + item.product" class="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition">
                <td class="p-4 text-black ">{{ item.product }}</td>
                <td class="p-4 text-black ">{{ item.unit }}</td>
                <td class="p-4 text-black ">{{ item.category || '—' }}</td>
                <td class="p-4 text-right text-black ">{{ formatQty(item.qty) }}</td>
                <td class="p-4 text-right text-black ">{{ formatNumber(item.selling_price) }}</td>
                <td class="p-4 text-right text-black ">{{ formatNumber(item.cost_price) }}</td>
                <td class="p-4 text-right font-medium text-blue-700 dark:text-blue-400">{{ formatNumber(item.line_sales) }}</td>
                <td class="p-4 text-right font-medium text-red-700 dark:text-red-400">{{ formatNumber(item.line_cost) }}</td>
                <td class="p-4 text-right font-bold" :class="item.profit >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">
                  {{ formatNumber(item.profit) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div class="flex flex-col sm:flex-row justify-between items-center gap-6 mt-10 text-sm text-black ">
        <div>
          Showing
          <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
          to
          <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, groupedData.length) }}</span>
          of
          <span class="font-medium">{{ groupedData.length }}</span> invoices
        </div>

        <div class="flex items-center gap-4">
          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="px-5 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition font-medium"
          >
            Previous
          </button>

          <span class="font-medium">
            Page {{ currentPage }} of {{ totalPages }}
          </span>

          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="px-5 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition font-medium"
          >
            Next
          </button>

          <select
            v-model="itemsPerPage"
            class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option :value="5">5 per page</option>
            <option :value="10">10 per page</option>
            <option :value="20">20 per page</option>
            <option :value="50">50 per page</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import debounce from 'lodash.debounce'
import api from '@/api'

const search = ref('')
const startDate = ref('')
const endDate = ref('')
const quickRange = ref('')
const rawData = ref([])
const totals = ref({})
const loading = ref(false)

const currentPage = ref(1)
const itemsPerPage = ref(10)

const debouncedFetchData = debounce(fetchData, 500)
const summary = ref({
  total_sales: 0,
  total_credit_sales: 0,
  outstanding_balance: 0,
  total_cash_received: 0,
  total_cogs: 0,
  gross_profit: 0,
  total_expenses: 0,
  net_profit: 0
})

async function fetchData() {
  loading.value = true
  currentPage.value = 1 // reset to page 1 on filter change

  try {
    const params = {}
    if (search.value.trim()) params.search = search.value.trim()
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const res = await api.get('/reports/sales-profit', { params })

    rawData.value = res.data.data || []
    totals.value = res.data.totals || {}
    summary.value = res.data.summary || {}   // ← new key from backend

  } catch (err) {
    console.error('Failed to load sales profit report:', err)
    rawData.value = []
  } finally {
    loading.value = false
  }
}
// const displaySummary = computed(() => ({
//   total_sales: summary.value.total_sales ?? 0,
//   total_credit_sales: summary.value.total_credit_sales ?? 0,
//   outstanding_balance: summary.value.outstanding_balance ?? 0,
//   total_cash_received: summary.value.total_cash_received ?? 0,
//   total_cogs: summary.value.total_cogs ?? 0,
//   gross_profit: summary.value.gross_profit ?? 0,
//   total_expenses: summary.value.total_expenses ?? 0,
//   net_profit: summary.value.net_profit ?? 0
// }))
const groupedData = computed(() => {
  const groups = {}
  rawData.value.forEach(row => {
    const key = row.invoice_number
    if (!groups[key]) {
      groups[key] = {
        invoice: row.invoice_number,
        sale_id: row.sale_id,
        date: row.sale_date ? new Date(row.sale_date).toLocaleDateString('en-GB', {
          day: 'numeric',
          month: 'short',
          year: 'numeric'
        }) : '—',
        customer: row.customer || 'Walk-in',
        sales_total: 0,
        cost_total: 0,
        profit_total: 0,
        items: []
      }
    }

    const sales = Number(row.line_sales || 0)
    const cost = Number(row.line_cost || 0)
    const profit = Number(row.profit || 0)

    groups[key].sales_total += sales
    groups[key].cost_total += cost
    groups[key].profit_total += profit

    groups[key].items.push({
      ...row,
      line_sales: sales,
      line_cost: cost,
      profit
    })
  })

  return Object.values(groups).sort((a, b) => new Date(b.date) - new Date(a.date))
})

const totalPages = computed(() => Math.ceil(groupedData.value.length / itemsPerPage.value))

const paginatedGroupedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return groupedData.value.slice(start, end)
})
// const displaySummary = computed(() => ({
//   total_sales: summary.value.total_sales ?? 0,
//   total_credit_sales: summary.value.total_credit_sales ?? 0,
//   outstanding_balance: summary.value.outstanding_balance ?? 0,
//   total_cash_received: summary.value.total_cash_received ?? 0,
//   total_cogs: summary.value.total_cogs ?? 0,
//   gross_profit: summary.value.gross_profit ?? 0,
//   total_expenses: summary.value.total_expenses ?? 0,
//   net_profit: summary.value.net_profit ?? 0
// }))
function applyQuickRange() {
  const today = new Date()
  let start = ''
  let end = today.toISOString().split('T')[0]

  switch (quickRange.value) {
    case 'today':
      start = end
      break
    case 'yesterday': {
      const yest = new Date(today)
      yest.setDate(today.getDate() - 1)
      start = end = yest.toISOString().split('T')[0]
      break
    }
    case 'this-week': {
      const first = new Date(today)
      first.setDate(today.getDate() - today.getDay())
      start = first.toISOString().split('T')[0]
      break
    }
    case 'last-7-days': {
      const last7 = new Date(today)
      last7.setDate(today.getDate() - 7)
      start = last7.toISOString().split('T')[0]
      break
    }
    case 'this-month':
      start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
      break
    case 'last-30-days': {
      const last30 = new Date(today)
      last30.setDate(today.getDate() - 30)
      start = last30.toISOString().split('T')[0]
      break
    }
  }

  startDate.value = start
  endDate.value = end
  fetchData()
}

watch([itemsPerPage], () => {
  currentPage.value = 1
})

const formatNumber = (num) =>
  Number(num || 0).toLocaleString('en-UG', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })

const formatQty = (num) =>
  Number(num || 0).toLocaleString('en-UG', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3
  })

onMounted(fetchData)
</script>

<style scoped>
/* Fade-in animation */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.5s ease-out forwards;
}

/* Smooth hover on rows */
.hover\:bg-indigo-50\/30:hover {
  background-color: rgba(99, 102, 241, 0.1);
}
.dark .hover\:bg-gray-800\/50:hover {
  background-color: rgba(31, 41, 55, 0.5);
}
</style>
