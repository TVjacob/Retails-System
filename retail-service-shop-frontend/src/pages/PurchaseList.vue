<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Purchase Orders</h1>

    <!-- Tabs -->
    <div class="flex space-x-4 mb-6">
      <button
        :class="currentTab === 'paid' ? activeTabClass : inactiveTabClass"
        @click="currentTab = 'paid'"
      >
        Paid Invoices
      </button>
      <button
        :class="currentTab === 'unpaid' ? activeTabClass : inactiveTabClass"
        @click="currentTab = 'unpaid'"
      >
        Unpaid Invoices
      </button>
    </div>

    <!-- Export Buttons -->
    <div class="flex space-x-2 mb-4">
      <button
        @click="exportCSV"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded shadow transition transform hover:scale-105"
      >
        Export CSV
      </button>
      <button
        @click="exportPDF"
        class="px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded shadow transition transform hover:scale-105"
      >
        Export PDF
      </button>
    </div>

    <!-- Purchase Orders Table -->
    <div class="overflow-x-auto border rounded-lg shadow-lg bg-white">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-3 border-b text-left">PO ID</th>
            <th class="p-3 border-b text-left">Supplier</th>
            <th class="p-3 border-b text-left">Invoice Number</th>
            <th class="p-3 border-b text-left">Purchase Date</th>
            <th class="p-3 border-b text-right">Total Amount</th>
            <th class="p-3 border-b text-right">Paid</th>
            <th class="p-3 border-b text-right">Balance</th>
            <th class="p-3 border-b text-center">Status</th>
            <th class="p-3 border-b text-center w-[260px]">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="po in filteredPurchaseOrders"
            :key="po.id"
            class="hover:bg-gray-50 transition-all duration-300 ease-in-out"
          >
            <td class="p-3 border">{{ po.id }}</td>
            <td class="p-3 border">{{ po.supplier_name }}</td>
            <td class="p-3 border">{{ po.invoice_number }}</td>
            <td class="p-3 border">{{ formatDate(po.purchase_date) }}</td>
            <td class="p-3 border text-right">{{ po.total_amount.toFixed(2) }}</td>
            <td class="p-3 border text-right">{{ po.total_paid.toFixed(2) }}</td>
            <td class="p-3 border text-right">{{ po.total_balance.toFixed(2) }}</td>
            <td class="p-3 border text-center">
              <span
                :class="po.total_balance === 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'"
              >
                {{ po.total_balance === 0 ? 'Paid' : 'Unpaid' }}
              </span>
            </td>
            <td class="p-3 border text-center">
              <div class="flex justify-center items-center space-x-2">
                <button
                  v-if="po.total_balance > 0"
                  @click="openPaymentModal(po)"
                  class="action-btn bg-green-600 hover:bg-green-700"
                  title="Make Payment"
                >
                  💰
                </button>

                <router-link
                  :to="`/purchase-orders/${po.id}/edit`"
                  class="action-btn bg-yellow-500 hover:bg-yellow-600"
                  title="Edit"
                >
                  ✏️
                </router-link>

                <router-link
                  :to="`/purchase-orders/${po.id}`"
                  class="action-btn bg-blue-500 hover:bg-blue-600"
                  title="View"
                >
                  🔍
                </router-link>

                <button
                  @click="confirmDelete(po)"
                  class="action-btn bg-red-600 hover:bg-red-700"
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Payment Modal -->
    <PaymentPurchaseModal
      v-model:modelValue="showPaymentModal"
      :po="selectedPO"
      :accounts="accounts"
      @saved="refreshPurchaseOrders"
    />

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg shadow-lg p-6 w-[400px] text-center">
        <h2 class="text-xl font-bold mb-4 text-gray-800">Confirm Deletion</h2>
        <p class="text-gray-600 mb-6">
          Are you sure you want to delete
          <span class="font-semibold text-gray-900">PO #{{ selectedPO?.id }}</span>?
        </p>
        <div class="flex justify-center space-x-4">
          <button
            @click="deletePurchaseOrder"
            class="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded shadow"
          >
            Yes, Delete
          </button>
          <button
            @click="showDeleteModal = false"
            class="px-5 py-2 bg-gray-300 hover:bg-gray-400 rounded text-gray-800 shadow"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api';
import PaymentPurchaseModal from './PaymentPurchaseModal.vue';

// Tabs and data
const currentTab = ref('unpaid');
const purchaseOrders = ref([]);
const accounts = ref([]);
const showPaymentModal = ref(false);
const selectedPO = ref(null);
const showDeleteModal = ref(false);

// Classes
const activeTabClass =
  'px-4 py-2 rounded bg-indigo-600 text-white transition transform hover:scale-105';
const inactiveTabClass =
  'px-4 py-2 rounded bg-gray-200 text-gray-700 transition transform hover:scale-105';

// Fetch data
const fetchPurchaseOrders = async () => {
  try {
    const res = await api.get('/suppliers/orders');
    purchaseOrders.value = res.data.filter(po => po.status !== 9); // exclude deleted
  } catch (err) {
    console.error(err);
  }
};

const fetchAccounts = async () => {
  try {
    const res = await api.get('/accounts/cash-bank');
    accounts.value = res.data;
  } catch (err) {
    console.error(err);
  }
};

// Computed
const filteredPurchaseOrders = computed(() => {
  return currentTab.value === 'paid'
    ? purchaseOrders.value.filter(po => po.total_balance === 0)
    : purchaseOrders.value.filter(po => po.total_balance > 0);
});

const formatDate = dateStr => new Date(dateStr).toLocaleDateString();

// Actions
const openPaymentModal = po => {
  selectedPO.value = po;
  showPaymentModal.value = true;
};

const confirmDelete = po => {
  selectedPO.value = po;
  showDeleteModal.value = true;
};

const deletePurchaseOrder = async () => {
  if (!selectedPO.value) return;
  try {
    await api.put(`/suppliers/orders/${selectedPO.value.id}/delete`);
    showDeleteModal.value = false;
    await fetchPurchaseOrders();
  } catch (err) {
    console.error(err);
    alert('Error deleting purchase order.');
  }
};

const refreshPurchaseOrders = () => fetchPurchaseOrders();

// Export placeholders
const exportCSV = () => alert('CSV export not implemented yet!');
const exportPDF = () => alert('PDF export not implemented yet!');

onMounted(() => {
  fetchPurchaseOrders();
  fetchAccounts();
});
</script>

<style scoped>
/* Header animation */
@keyframes fadeIn {
  0% { opacity: 0; transform: translateY(-10px);}
  100% { opacity: 1; transform: translateY(0);}
}
.animate-fadeIn {
  animation: fadeIn 0.5s ease-in-out forwards;
}

/* Table hover effect */
tbody tr:hover {
  background-color: #f9fafb;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04);
}

/* Smooth button hover */
button, a {
  transition: all 0.25s ease-in-out;
}

/* Action buttons unified design */
.action-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  color: white;
  font-size: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.action-btn:hover {
  transform: scale(1.08);
}
</style>
