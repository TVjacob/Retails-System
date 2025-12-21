<template>
  <div class="p-6 max-w-7xl mx-auto animate-fadeIn">
    <!-- PAGE TITLE -->
    <h1 class="text-3xl font-bold mb-6 text-gray-800 tracking-tight">
      Sales Profit Report
    </h1>

    <!-- FILTERS -->
    <div class="bg-white p-5 rounded-xl shadow-md mb-6 grid grid-cols-1 md:grid-cols-4 gap-4 border border-gray-100">
      <!-- Search -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 mb-1">Search</label>
        <input
          v-model="search"
          @input="fetchData"
          placeholder="Search invoice, product, or customer..."
          class="border p-2 rounded-lg w-full focus:ring focus:ring-blue-300"
        />
      </div>

      <!-- Start Date -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 mb-1">Start Date</label>
        <input
          type="date"
          v-model="startDate"
          @change="fetchData"
          class="border p-2 rounded-lg w-full focus:ring focus:ring-blue-300"
        />
      </div>

      <!-- End Date -->
      <div class="flex flex-col">
        <label class="text-sm font-medium text-gray-600 mb-1">End Date</label>
        <input
          type="date"
          v-model="endDate"
          @change="fetchData"
          class="border p-2 rounded-lg w-full focus:ring focus:ring-blue-300"
        />
      </div>

      <!-- Refresh Button -->
      <div class="flex items-end">
        <button
          @click="fetchData"
          class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg w-full"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- TOP SUMMARY CARDS -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      <div class="bg-white shadow rounded-xl border p-4 text-center">
        <p class="text-sm font-medium text-gray-600">Total Invoices</p>
        <p class="text-2xl md:text-3xl font-bold text-indigo-600 mt-1">{{ groupedData.length }}</p>
      </div>
      <div class="bg-white shadow rounded-xl border p-4 text-center">
        <p class="text-sm font-medium text-gray-600">Total Sales</p>
        <p class="text-2xl md:text-3xl font-bold text-blue-600 mt-1">{{ formatNumber(totals.total_sales) }}</p>
      </div>
      <div class="bg-white shadow rounded-xl border p-4 text-center">
        <p class="text-sm font-medium text-gray-600">Total Cost</p>
        <p class="text-2xl md:text-3xl font-bold text-red-600 mt-1">{{ formatNumber(totals.total_cost) }}</p>
      </div>
      <div class="bg-white shadow rounded-xl border p-4 text-center">
        <p class="text-sm font-medium text-gray-600">Total Profit</p>
        <p class="text-2xl md:text-3xl font-bold mt-1" :class="totals.total_profit >=0 ? 'text-green-600' : 'text-red-600'">
          {{ formatNumber(totals.total_profit) }}
        </p>
      </div>
      <div class="bg-white shadow rounded-xl border p-4 text-center">
        <p class="text-sm font-medium text-gray-600">Cash Received</p>
        <p class="text-2xl md:text-3xl font-bold text-green-700 mt-1">{{ formatNumber(totals.total_cash_received) }}</p>
      </div>
      <div class="bg-white shadow rounded-xl border p-4 text-center">
        <p class="text-sm font-medium text-gray-600">Outstanding Credit</p>
        <p class="text-2xl md:text-3xl font-bold text-yellow-600 mt-1">{{ formatNumber(totals.total_credit_outstanding) }}</p>
      </div>
    </div>

    <!-- INVOICE GROUPS -->
    <div v-for="invoice in groupedData" :key="invoice.invoice" class="bg-white mb-6 p-4 shadow rounded-lg border">
      <!-- GROUP HEADER -->
      <div class="flex flex-col md:flex-row md:justify-between mb-3 border-b pb-2 gap-2">
        <div>
          <h2 class="text-lg font-bold">{{ invoice.invoice }}</h2>
          <p class="text-sm text-gray-600">Date: {{ invoice.date }}</p>
        </div>
        <div class="text-left md:text-right">
          <p class="text-sm font-semibold">Sales: <span class="text-blue-600">{{ formatNumber(invoice.sales_total) }}</span></p>
          <p class="text-sm font-semibold">Cost: <span class="text-red-600">{{ formatNumber(invoice.cost_total) }}</span></p>
          <p class="text-sm font-semibold">Profit: <span :class="invoice.profit_total >=0 ? 'text-green-600' : 'text-red-600'">{{ formatNumber(invoice.profit_total) }}</span></p>
        </div>
      </div>

      <!-- DETAILS TABLE -->
      <div class="overflow-x-auto">
        <table class="min-w-full border-collapse text-sm">
          <thead class="bg-gray-100 text-xs uppercase font-semibold">
            <tr>
              <th class="p-2 border text-left">Product</th>
              <th class="p-2 border text-left">Category</th>
              <th class="p-2 border text-right">Qty</th>
              <th class="p-2 border text-right">Sell Price</th>
              <th class="p-2 border text-right">Buy Price</th>
              <th class="p-2 border text-right">Line Sales</th>
              <th class="p-2 border text-right">Line Cost</th>
              <th class="p-2 border text-right">Profit</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in invoice.items" :key="item.id" class="hover:bg-gray-50 transition">
              <td class="p-2 border">{{ item.product }}</td>
              <td class="p-2 border">{{ item.category }}</td>
              <td class="p-2 border text-right">{{ formatQty(item.qty) }}</td>
              <td class="p-2 border text-right">{{ formatNumber(item.selling_price) }}</td>
              <td class="p-2 border text-right">{{ formatNumber(item.purchase_price) }}</td>
              <td class="p-2 border text-right">{{ formatNumber(item.line_sales) }}</td>
              <td class="p-2 border text-right">{{ formatNumber(item.line_cost) }}</td>
              <td class="p-2 border text-right font-bold" :class="item.profit >=0 ? 'text-green-600' : 'text-red-600'">{{ formatNumber(item.profit) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import api from "@/api";

const rawData = ref([]);
const totals = ref({});
const search = ref("");
const startDate = ref("");
const endDate = ref("");

const fetchData = async () => {
  try {
    const res = await api.get("/reports/sales-profit", {
      params: {
        search: search.value,
        start_date: startDate.value,
        end_date: endDate.value
      }
    });
    rawData.value = res.data.data || [];
    totals.value = res.data.totals || {};
  } catch (err) {
    console.error(err);
  }
};

/* GROUP BY INVOICE */
const groupedData = computed(() => {
  const groups = {};
  rawData.value.forEach(row => {
    if (!groups[row.invoice_number]) {
      groups[row.invoice_number] = {
        invoice: row.invoice_number,
        date: new Date(row.sale_date).toLocaleDateString(),
        sales_total: 0,
        cost_total: 0,
        profit_total: 0,
        items: []
      };
    }
    groups[row.invoice_number].sales_total += Number(row.line_sales || 0);
    groups[row.invoice_number].cost_total += Number(row.line_cost || 0);
    groups[row.invoice_number].profit_total += Number(row.profit || 0);
    groups[row.invoice_number].items.push(row);
  });
  return Object.values(groups);
});

const formatQty = (num) => Number(num || 0).toLocaleString(undefined, { minimumFractionDigits:0, maximumFractionDigits:0 });
const formatNumber = (num) => Number(num || 0).toLocaleString(undefined, { minimumFractionDigits:2, maximumFractionDigits:2 });

onMounted(fetchData);
</script>

<style scoped>
@keyframes fadeIn {
  0% { opacity: 0; transform: translateY(8px);}
  100% { opacity: 1; transform: translateY(0);}
}
.animate-fadeIn { animation: fadeIn 0.4s ease-out forwards; }
</style>
