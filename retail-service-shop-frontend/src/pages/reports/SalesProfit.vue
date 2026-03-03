<template>
  <div class="p-6 max-w-7xl mx-auto animate-fadeIn">
    <!-- PAGE TITLE -->
    <h1 class="text-3xl font-bold mb-6 text-gray-800 dark:text-gray-100 tracking-tight">
      Sales Profit Report
    </h1>

    <!-- FILTERS -->
    <div class="bg-white dark:bg-gray-800 p-5 rounded-xl shadow-md mb-6 grid grid-cols-1 md:grid-cols-5 gap-4 border border-gray-100 dark:border-gray-700">
      <!-- Search -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Search</label>
        <input
          v-model="search"
          @input="debouncedFetchData"
          placeholder="Search invoice, product, customer..."
          class="border dark:border-gray-600 p-2 rounded-lg w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring focus:ring-blue-300 dark:focus:ring-blue-500"
        />
      </div>

      <!-- Start Date -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Start Date</label>
        <input
          type="date"
          v-model="startDate"
          @change="fetchData"
          class="border dark:border-gray-600 p-2 rounded-lg w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring focus:ring-blue-300 dark:focus:ring-blue-500"
        />
      </div>

      <!-- End Date -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">End Date</label>
        <input
          type="date"
          v-model="endDate"
          @change="fetchData"
          class="border dark:border-gray-600 p-2 rounded-lg w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring focus:ring-blue-300 dark:focus:ring-blue-500"
        />
      </div>

      <!-- Quick Range -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Quick Range</label>
        <select
          v-model="quickRange"
          @change="applyQuickRange"
          class="border dark:border-gray-600 p-2 rounded-lg w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring focus:ring-blue-300 dark:focus:ring-blue-500"
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

      <!-- Refresh Button -->
      <div class="flex items-end">
        <button
          @click="fetchData"
          class="bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600 text-white font-semibold px-4 py-2 rounded-lg w-full transition"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- SUMMARY CARDS -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      <div class="bg-white dark:bg-gray-800 shadow rounded-xl border dark:border-gray-700 p-4 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Invoices</p>
        <p class="text-2xl md:text-3xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
          {{ groupedData.length }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-xl border dark:border-gray-700 p-4 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Sales</p>
        <p class="text-2xl md:text-3xl font-bold text-blue-600 dark:text-blue-400 mt-1">
          {{ formatNumber(totals.total_sales) }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-xl border dark:border-gray-700 p-4 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Cost</p>
        <p class="text-2xl md:text-3xl font-bold text-red-600 dark:text-red-400 mt-1">
          {{ formatNumber(totals.total_cost) }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-xl border dark:border-gray-700 p-4 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Profit</p>
        <p
          class="text-2xl md:text-3xl font-bold mt-1"
          :class="totals.total_profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
        >
          {{ formatNumber(totals.total_profit) }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-xl border dark:border-gray-700 p-4 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Cash Received</p>
        <p class="text-2xl md:text-3xl font-bold text-green-700 dark:text-green-400 mt-1">
          {{ formatNumber(totals.total_cash_received) }}
        </p>
      </div>
      <div class="bg-white dark:bg-gray-800 shadow rounded-xl border dark:border-gray-700 p-4 text-center">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Outstanding Credit</p>
        <p class="text-2xl md:text-3xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">
          {{ formatNumber(totals.total_credit_outstanding) }}
        </p>
      </div>
    </div>

    <!-- LOADING / NO DATA -->
    <div v-if="loading" class="text-center py-12 text-gray-500 dark:text-gray-400">
      Loading...
    </div>
    <div v-else-if="groupedData.length === 0" class="text-center py-12 text-gray-500 dark:text-gray-400">
      No sales found for the selected filters
    </div>

    <!-- INVOICE GROUPS -->
    <div
      v-else
      v-for="invoice in groupedData"
      :key="invoice.invoice"
      class="bg-white dark:bg-gray-800 mb-6 p-4 shadow rounded-lg border dark:border-gray-700"
    >
      <!-- GROUP HEADER -->
      <div class="flex flex-col md:flex-row md:justify-between mb-3 border-b dark:border-gray-700 pb-2 gap-2">
        <div>
          <h2 class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ invoice.invoice }}</h2>
          <p class="text-sm text-gray-600 dark:text-gray-400">Date: {{ invoice.date }}</p>
          <p class="text-sm text-gray-600 dark:text-gray-400">Customer: {{ invoice.customer }}</p>
        </div>
        <div class="text-left md:text-right flex items-center gap-4">
          <div class="text-right">
            <p class="text-sm font-semibold">
              Sales: <span class="text-blue-600 dark:text-blue-400">{{ formatNumber(invoice.sales_total) }}</span>
            </p>
            <p class="text-sm font-semibold">
              Cost: <span class="text-red-600 dark:text-red-400">{{ formatNumber(invoice.cost_total) }}</span>
            </p>
            <p class="text-sm font-semibold">
              Profit:
              <span
                :class="invoice.profit_total >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
              >
                {{ formatNumber(invoice.profit_total) }}
              </span>
            </p>
          </div>

          <router-link
            :to="`/editsales/${invoice.sale_id}`"
            class="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 shadow-sm"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit
          </router-link>
        </div>
      </div>

      <!-- TABLE -->
      <div class="overflow-x-auto">
        <table class="min-w-full border-collapse text-sm">
          <thead class="bg-gray-100 dark:bg-gray-700 text-xs uppercase font-semibold text-gray-700 dark:text-gray-300">
            <tr>
              <th class="p-2 border dark:border-gray-600 text-left">Product</th>
              <th class="p-2 border dark:border-gray-600 text-left">Unit</th>
              <th class="p-2 border dark:border-gray-600 text-left">Category</th>
              <th class="p-2 border dark:border-gray-600 text-right">Qty</th>
              <th class="p-2 border dark:border-gray-600 text-right">Sell Price</th>
              <th class="p-2 border dark:border-gray-600 text-right">Buy Price</th>
              <th class="p-2 border dark:border-gray-600 text-right">Line Sales</th>
              <th class="p-2 border dark:border-gray-600 text-right">Line Cost</th>
              <th class="p-2 border dark:border-gray-600 text-right">Profit</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in invoice.items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-700 transition">
              <td class="p-2 border dark:border-gray-600">{{ item.product }}</td>
              <td class="p-2 border dark:border-gray-600">{{ item.unit }}</td>
              <td class="p-2 border dark:border-gray-600">{{ item.category }}</td>
              <td class="p-2 border dark:border-gray-600 text-right">{{ formatQty(item.qty) }}</td>
              <td class="p-2 border dark:border-gray-600 text-right">{{ formatNumber(item.selling_price) }}</td>
              <td class="p-2 border dark:border-gray-600 text-right">{{ formatNumber(item.purchase_price) }}</td>
              <td class="p-2 border dark:border-gray-600 text-right">{{ formatNumber(item.line_sales) }}</td>
              <td class="p-2 border dark:border-gray-600 text-right">{{ formatNumber(item.line_cost) }}</td>
              <td class="p-2 border dark:border-gray-600 text-right font-bold" :class="item.profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                {{ formatNumber(item.profit) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import debounce from 'lodash.debounce';   // Fixed: using your existing lodash.debounce package
import api from '@/api';

const search = ref('');
const startDate = ref('');
const endDate = ref('');
const quickRange = ref('');
const rawData = ref([]);
const totals = ref({});
const loading = ref(false);

const debouncedFetchData = debounce(fetchData, 500);

async function fetchData() {
  loading.value = true;
  try {
    const params = {};
    if (search.value.trim()) params.search = search.value.trim();
    if (startDate.value) params.start_date = startDate.value;
    if (endDate.value) params.end_date = endDate.value;

    // Debug log – remove in production if not needed
    console.log('Fetching sales report with params:', params);

    const res = await api.get('/reports/sales-profit', { params });

    rawData.value = res.data.data || [];
    totals.value = res.data.totals || {};
  } catch (err) {
    console.error('Failed to load sales profit report:', err);
  } finally {
    loading.value = false;
  }
}

const groupedData = computed(() => {
  const groups = {};
  rawData.value.forEach(row => {
    const key = row.invoice_number;
    if (!groups[key]) {
      groups[key] = {
        invoice: row.invoice_number,
        sale_id: row.sale_id,
        date: row.sale_date ? new Date(row.sale_date).toLocaleDateString() : '—',
        customer: row.customer || 'Walk-in',
        sales_total: 0,
        cost_total: 0,
        profit_total: 0,
        items: []
      };
    }

    const sales = Number(row.line_sales || 0);
    const cost = Number(row.line_cost || 0);
    const profit = Number(row.profit || 0);

    groups[key].sales_total += sales;
    groups[key].cost_total += cost;
    groups[key].profit_total += profit;

    groups[key].items.push({
      ...row,
      line_sales: sales,
      line_cost: cost,
      profit
    });
  });

  // Sort newest first (optional – remove .sort() if you prefer original order)
  return Object.values(groups).sort((a, b) => new Date(b.date) - new Date(a.date));
});

function applyQuickRange() {
  const today = new Date();
  let start = '';
  let end = '';

  switch (quickRange.value) {
    case 'today':
      start = end = today.toISOString().split('T')[0];
      break;
    case 'yesterday':
      const yesterday = new Date(today);
      yesterday.setDate(today.getDate() - 1);
      start = end = yesterday.toISOString().split('T')[0];
      break;
    case 'this-week':
      const first = new Date(today);
      first.setDate(today.getDate() - today.getDay());
      start = first.toISOString().split('T')[0];
      end = today.toISOString().split('T')[0];
      break;
    case 'last-7-days':
      const last7 = new Date(today);
      last7.setDate(today.getDate() - 7);
      start = last7.toISOString().split('T')[0];
      end = today.toISOString().split('T')[0];
      break;
    case 'this-month':
      start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
      end = today.toISOString().split('T')[0];
      break;
    case 'last-30-days':
      const last30 = new Date(today);
      last30.setDate(today.getDate() - 30);
      start = last30.toISOString().split('T')[0];
      end = today.toISOString().split('T')[0];
      break;
    default:
      return;
  }

  startDate.value = start;
  endDate.value = end;
  fetchData();
}

// Formatters
const formatNumber = (num) =>
  Number(num || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const formatQty = (num) =>
  Number(num || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });

onMounted(fetchData);
</script>

<style scoped>
@keyframes fadeIn {
  0% {
    opacity: 0;
    transform: translateY(8px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
.animate-fadeIn {
  animation: fadeIn 0.4s ease-out forwards;
}
</style>