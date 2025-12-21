<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">

    <!-- Page Title -->
    <h1 class="text-3xl font-bold text-gray-800 animate-fadeIn">
      Purchased Products Report
    </h1>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-xl shadow flex flex-col md:flex-row gap-4 items-end">
      <div class="w-full md:w-1/3">
        <label class="text-sm font-medium text-gray-600">Search</label>
        <input
          v-model="search"
          @input="onFilterChange"
          placeholder="Search by product, invoice, supplier..."
          class="input-field"
        />
      </div>

      <div>
        <label class="text-sm font-medium text-gray-600">Start Date</label>
        <input
          type="date"
          v-model="startDate"
          @change="onFilterChange"
          class="input-field"
        />
      </div>

      <div>
        <label class="text-sm font-medium text-gray-600">End Date</label>
        <input
          type="date"
          v-model="endDate"
          @change="onFilterChange"
          class="input-field"
        />
      </div>
    </div>

    <!-- Summary Totals -->
    <div
      v-if="totals"
      class="grid md:grid-cols-2 gap-4 bg-white p-5 rounded-xl shadow border border-gray-200"
    >
      <div class="summary-card bg-indigo-50">
        <p class="text-sm text-gray-600">Total Quantity Purchased</p>
        <h2 class="summary-value text-indigo-700">
          {{ formatNumber(totals.total_quantity) }}
        </h2>
      </div>

      <div class="summary-card bg-green-50">
        <p class="text-sm text-gray-600">Total Amount Spent</p>
        <h2 class="summary-value text-green-700">
          {{ formatCurrency(totals.total_amount) }}
        </h2>
      </div>
    </div>

    <!-- Report Table -->
    <div class="overflow-x-auto bg-white rounded-xl shadow border">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100 text-sm uppercase tracking-wide">
          <tr>
            <th class="th-cell">PO ID</th>
            <th class="th-cell">Product</th>
            <th class="th-cell">Category</th>
            <th class="th-cell">Supplier</th>
            <th class="th-cell">Invoice</th>
            <th class="th-cell">Date</th>
            <th class="th-cell text-right">Qty</th>
            <th class="th-cell text-right">Unit Price</th>
            <th class="th-cell text-right">Total</th>
            <th class="th-cell text-center w-[150px]">Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="row in reportData"
            :key="row.purchase_id"
            class="hover:bg-gray-50 transition"
          >
            <td class="td-cell">{{ row.purchase_id }}</td>
            <td class="td-cell">{{ row.product }}</td>
            <td class="td-cell">{{ row.category }}</td>
            <td class="td-cell">{{ row.supplier }}</td>
            <td class="td-cell">{{ row.invoice_number }}</td>
            <td class="td-cell">{{ formatDate(row.purchase_date) }}</td>
            <td class="td-cell text-right">{{ formatNumber(row.qty) }}</td>
            <td class="td-cell text-right">{{ formatCurrency(row.unit_price) }}</td>
            <td class="td-cell text-right">{{ formatCurrency(row.total_price) }}</td>

            <td class="td-cell text-center">
              <div class="flex gap-2 justify-center">
                <!-- View -->
                <router-link
                  :to="`/purchase-orders/${row.purchase_id}`"
                  class="action-btn bg-blue-600 hover:bg-blue-700"
                  title="View"
                >
                  🔍
                </router-link>

                <!-- Edit -->
                <router-link
                  :to="`/purchase-orders/${row.purchase_id}/edit`"
                  class="action-btn bg-yellow-500 hover:bg-yellow-600"
                  title="Edit"
                >
                  ✏️
                </router-link>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="totalRecords > perPage"
      class="flex justify-between items-center p-3 bg-white rounded-xl shadow"
    >
      <button
        @click="prevPage"
        :disabled="page === 1"
        class="page-btn"
      >
        Prev
      </button>

      <span class="font-semibold">
        Page {{ page }}
      </span>

      <button
        @click="nextPage"
        :disabled="page >= Math.ceil(totalRecords / perPage)"
        class="page-btn"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";

const reportData = ref([]);
const totals = ref(null);

const page = ref(1);
const perPage = 100;
const totalRecords = ref(0);

const search = ref("");
const startDate = ref("");
const endDate = ref("");

let searchTimeout;

const onFilterChange = () => {
  page.value = 1;
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(fetchData, 300);
};

const fetchData = async () => {
  try {
    const res = await api.get("/reports/purchased-product", {
      params: {
        page: page.value,
        search: search.value || "",
        start_date: startDate.value || "",
        end_date: endDate.value || ""
      }
    });

    reportData.value = res.data.data || [];
    totalRecords.value = res.data.total_records || 0;
    totals.value = res.data.totals || {};

  } catch (err) {
    console.error(err);
  }
};

const nextPage = () => {
  if (page.value < Math.ceil(totalRecords.value / perPage)) {
    page.value++;
    fetchData();
  }
};

const prevPage = () => {
  if (page.value > 1) {
    page.value--;
    fetchData();
  }
};

const formatDate = d => new Date(d).toLocaleDateString();

const formatNumber = num => {
  if (num == null) return "0";
  return Number(num).toLocaleString();
};

const formatCurrency = num => {
  if (num == null) return "0.00";
  return Number(num).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
/* Fade-in animation */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.4s ease-in-out forwards;
}

/* Inputs */
.input-field {
  border: 1px solid #d1d5db;
  padding: 8px 10px;
  width: 100%;
  border-radius: 8px;
  transition: 0.2s;
}
.input-field:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99,102,241,0.25);
}

/* Table */
.th-cell {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}
.td-cell {
  padding: 12px;
  border-bottom: 1px solid #f1f1f1;
}

/* Totals Cards */
.summary-card {
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}
.summary-value {
  font-size: 2rem;
  font-weight: 800;
}

/* Action Buttons */
.action-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  color: white;
  font-size: 16px;
  transition: 0.2s;
}
.action-btn:hover {
  transform: scale(1.08);
}

/* Pagination */
.page-btn {
  padding: 8px 16px;
  background: #e5e7eb;
  border-radius: 8px;
  transition: 0.2s;
}
.page-btn:hover:not(:disabled) {
  background: #d1d5db;
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
