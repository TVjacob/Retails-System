<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Purchase Orders</h1>

    <!-- Tabs -->
    <div class="flex space-x-4 mb-6">
      <button
        :class="currentTab === 'paid' ? activeTabClass : inactiveTabClass"
        @click="changeTab('paid')"
      >
        Paid Invoices
      </button>
      <button
        :class="currentTab === 'unpaid' ? activeTabClass : inactiveTabClass"
        @click="changeTab('unpaid')"
      >
        Unpaid Invoices
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-4 mb-6 items-center">
      <input
        v-model="productSearchQuery"
        @input="onProductSearch"
        placeholder="🔍 Search product, supplier, invoice or memo"
        class="flex-1 min-w-[280px] px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <input
        type="date"
        v-model="startDate"
        @change="onFilterChange"
        class="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <input
        type="date"
        v-model="endDate"
        @change="onFilterChange"
        class="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <button
        @click="fetchPurchaseOrders"
        class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow transition transform hover:scale-105"
      >
        Apply
      </button>
    </div>

    <!-- Export Buttons -->
    <div class="flex space-x-3 mb-6">
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

    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg shadow-lg bg-white">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-3 border-b text-left font-semibold">PO ID</th>
            <th class="p-3 border-b text-left font-semibold">Supplier</th>
            <th class="p-3 border-b text-left font-semibold">Invoice #</th>
            <th class="p-3 border-b text-left font-semibold">Purchase Date</th>
            <th class="p-3 border-b text-right font-semibold">Total</th>
            <th class="p-3 border-b text-right font-semibold">Paid</th>
            <th class="p-3 border-b text-right font-semibold">Balance</th>
            <th class="p-3 border-b text-center font-semibold">Status</th>
            <th class="p-3 border-b text-center font-semibold w-[260px]">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="po in filteredPurchaseOrders"
            :key="po.id"
            class="hover:bg-gray-50 transition-all duration-200 ease-in-out cursor-pointer"
          >
            <td class="p-3 border">{{ po.id }}</td>
            <td class="p-3 border">{{ po.supplier_name }}</td>
            <td class="p-3 border">{{ po.invoice_number }}</td>
            <td class="p-3 border">{{ formatDate(po.purchase_date) }}</td>
            <td class="p-3 border text-right">{{ formatPrice(po.total_amount) }}</td>
            <td class="p-3 border text-right">{{ formatPrice(po.total_paid) }}</td>
            <td class="p-3 border text-right">{{ formatPrice(po.total_balance) }}</td>
            <td class="p-3 border text-center">
              <span
                :class="po.total_balance === 0 ? 'text-green-700 font-bold' : 'text-red-700 font-bold'"
              >
                {{ po.total_balance === 0 ? 'Paid' : 'Unpaid' }}
              </span>
            </td>
            <td class="p-3 border text-center">
              <div class="flex justify-center items-center space-x-2 flex-wrap gap-y-1">
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
          <tr v-if="filteredPurchaseOrders.length === 0">
            <td colspan="9" class="p-8 text-center text-gray-500 italic">
              No purchase orders found matching your filters.
            </td>
          </tr>
        </tbody>

        <!-- Totals -->
        <tfoot class="bg-gray-100 font-bold">
          <tr>
            <td colspan="4" class="p-3 text-right border-t">Totals:</td>
            <td class="p-3 text-right border-t">{{ formatPrice(totalAmount) }}</td>
            <td class="p-3 text-right border-t">{{ formatPrice(totalPaid) }}</td>
            <td class="p-3 text-right border-t">{{ formatPrice(totalBalance) }}</td>
            <td colspan="2" class="p-3 border-t"></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Modals -->
    <PaymentPurchaseModal
      v-model:modelValue="showPaymentModal"
      :po="selectedPO"
      :accounts="accounts"
      @saved="refreshPurchaseOrders"
    />

    <!-- Delete Confirmation -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
        <h2 class="text-xl font-bold text-gray-800 mb-4">Confirm Deletion</h2>
        <p class="text-gray-600 mb-6">
          Are you sure you want to delete
          <strong>PO #{{ selectedPO?.id }}</strong
          >?
        </p>
        <div class="flex justify-end space-x-3">
          <button
            @click="showDeleteModal = false"
            class="px-5 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium"
          >
            Cancel
          </button>
          <button
            @click="deletePurchaseOrder"
            class="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium shadow"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import debounce from 'lodash.debounce';
import api from '../api';
import PaymentPurchaseModal from './PaymentPurchaseModal.vue';

const currentTab = ref('unpaid');
const purchaseOrders = ref([]);
const accounts = ref([]);
const showPaymentModal = ref(false);
const selectedPO = ref(null);
const showDeleteModal = ref(false);

const productSearchQuery = ref('');
const startDate = ref(new Date().toISOString().split('T')[0]);
const endDate = ref(new Date().toISOString().split('T')[0]);

const activeTabClass =
  'px-5 py-2 rounded-lg bg-indigo-600 text-white font-medium transition hover:scale-105 shadow-sm';
const inactiveTabClass =
  'px-5 py-2 rounded-lg bg-gray-200 text-gray-700 font-medium transition hover:bg-gray-300 hover:scale-105';

const fetchPurchaseOrders = async () => {
  try {
    const params = {
      search: productSearchQuery.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
    };
    const res = await api.get('/suppliers/orders', { params });
    purchaseOrders.value = res.data.filter(po => po.status !== 9); // exclude deleted/soft-deleted
  } catch (err) {
    console.error('Failed to load purchase orders', err);
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

const filteredPurchaseOrders = computed(() => {
  return currentTab.value === 'paid'
    ? purchaseOrders.value.filter(po => po.total_balance === 0)
    : purchaseOrders.value.filter(po => po.total_balance > 0);
});

const totalAmount = computed(() =>
  filteredPurchaseOrders.value.reduce((sum, po) => sum + Number(po.total_amount || 0), 0)
);
const totalPaid = computed(() =>
  filteredPurchaseOrders.value.reduce((sum, po) => sum + Number(po.total_paid || 0), 0)
);
const totalBalance = computed(() =>
  filteredPurchaseOrders.value.reduce((sum, po) => sum + Number(po.total_balance || 0), 0)
);

const formatDate = (dateStr) => (dateStr ? new Date(dateStr).toLocaleDateString('en-GB') : '-');
const formatPrice = (val) => Number(val || 0).toLocaleString('en-UG', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const changeTab = (tab) => {
  currentTab.value = tab;
};

const openPaymentModal = (po) => {
  selectedPO.value = po;
  showPaymentModal.value = true;
};

const confirmDelete = (po) => {
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
    console.error('Delete failed', err);
    alert('Could not delete purchase order. Please try again.');
  }
};

const refreshPurchaseOrders = () => fetchPurchaseOrders();

const exportCSV = () => alert('CSV export coming soon!');
const exportPDF = () => alert('PDF export coming soon!');

const onProductSearch = debounce(fetchPurchaseOrders, 420);
const onFilterChange = debounce(fetchPurchaseOrders, 500);

onMounted(() => {
  fetchPurchaseOrders();
  fetchAccounts();
});
</script>

<style scoped>
@keyframes fadeIn {
  0% { opacity: 0; transform: translateY(-12px); }
  100% { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.6s ease-out forwards;
}

.action-btn {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  color: white;
  font-size: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: scale(1.12);
  box-shadow: 0 3px 8px rgba(0,0,0,0.2);
}

tbody tr:hover {
  background-color: #f8fafc;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
</style>