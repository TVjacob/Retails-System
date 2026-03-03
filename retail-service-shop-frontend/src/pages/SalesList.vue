<template>
  <div class="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Sales List</h1>

    <!-- Tabs + Filters -->
    <div class="flex flex-wrap gap-3 mb-6 items-center">
      <button
        :class="currentTab === 'paid' ? activeTabClass : inactiveTabClass"
        @click="currentTab = 'paid'"
      >
        Paid Sales
      </button>
      <button
        :class="currentTab === 'unpaid' ? activeTabClass : inactiveTabClass"
        @click="currentTab = 'unpaid'"
      >
        Unpaid Sales
      </button>

      <input
        v-model="searchQuery"
        @input="debouncedFetchSales"
        placeholder="🔍 Search sale #, customer, memo..."
        class="flex-1 min-w-[240px] px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <input
        type="date"
        v-model="startDate"
        @change="debouncedFetchSales"
        class="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />
      <input
        type="date"
        v-model="endDate"
        @change="debouncedFetchSales"
        class="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <button
        @click="fetchSales"
        class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow transition"
      >
        Refresh
      </button>
    </div>

    <!-- Totals -->
    <div class="mb-5 flex flex-wrap justify-end gap-6 font-semibold text-gray-800">
      <div>Total Amount: <span class="text-indigo-700">{{ formatCurrency(totalAmount) }}</span></div>
      <div>Total Paid: <span class="text-green-700">{{ formatCurrency(totalPaid) }}</span></div>
      <div>Total Balance: <span class="text-red-700">{{ formatCurrency(totalBalance) }}</span></div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto bg-white rounded-xl shadow border border-gray-200">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100 text-gray-700 sticky top-0 z-10">
          <tr>
            <th class="p-3 border-b text-left font-semibold">Sale ID</th>
            <th class="p-3 border-b text-left font-semibold">Sale Number</th>
            <th class="p-3 border-b text-left font-semibold">Memo</th>
            <th class="p-3 border-b text-left font-semibold">Customer</th>
            <th class="p-3 border-b text-left font-semibold">Sale Date</th>
            <th class="p-3 border-b text-right font-semibold">Total</th>
            <th class="p-3 border-b text-right font-semibold">Paid</th>
            <th class="p-3 border-b text-right font-semibold">Balance</th>
            <th class="p-3 border-b text-center font-semibold">Status</th>
            <th class="p-3 border-b text-center font-semibold w-64">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="sale in filteredSales"
            :key="sale.sale_id"
            class="hover:bg-gray-50 transition-colors"
          >
            <td class="p-3 border-b">{{ sale.sale_id }}</td>
            <td class="p-3 border-b font-medium">{{ sale.sale_number }}</td>
            <td class="p-3 border-b text-gray-600">{{ sale.memo || '—' }}</td>
            <td class="p-3 border-b">{{ sale.customer_name || sale.customer?.name || '—' }}</td>
            <td class="p-3 border-b">{{ formatDate(sale.sale_date) }}</td>
            <td class="p-3 border-b text-right">{{ formatCurrency(sale.total_amount) }}</td>
            <td class="p-3 border-b text-right">{{ formatCurrency(sale.total_paid || 0) }}</td>
            <td class="p-3 border-b text-right font-semibold" :class="sale.balance <= 0 ? 'text-green-700' : 'text-red-700'">
              {{ formatCurrency(sale.balance) }}
            </td>
            <td class="p-3 border-b text-center">
              <span
                :class="sale.balance <= 0
                  ? 'bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium'
                  : 'bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium'"
              >
                {{ sale.balance <= 0 ? 'Paid' : 'Unpaid' }}
              </span>
            </td>
            <td class="p-3 border-b text-center flex flex-wrap justify-center gap-2">
              <router-link
                :to="`/editsales/${sale.sale_id}`"
                class="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg text-sm transition flex items-center gap-1 shadow-sm"
              >
                ✏️ Edit
              </router-link>

              <button
                v-if="sale.balance > 0"
                @click="openPaymentModal(sale)"
                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-sm transition shadow-sm"
              >
                💰 Receive
              </button>

              <button
                @click="previewPaymentReport(sale.sale_id)"
                class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm transition shadow-sm"
              >
                🔍 Report
              </button>

              <button
                @click="confirmDeleteSale(sale)"
                class="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg text-sm transition shadow-sm"
              >
                🗑️ Delete
              </button>
            </td>
          </tr>

          <tr v-if="filteredSales.length === 0">
            <td colspan="10" class="p-12 text-center text-gray-500 italic">
              No sales found matching your filters.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modals -->
    <PaymentModal
      v-model:modelValue="showPaymentModal"
      :sale="selectedSale"
      :accounts="accounts"
      @saved="fetchSales"
    />

    <ReportModal
      v-model:show="showReportModal"
      :report="paymentReport"
    />

    <!-- Toast -->
    <div
      v-if="toast.visible"
      class="fixed bottom-6 right-6 z-50 bg-gray-900 text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-fade-in-up"
    >
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import debounce from 'lodash.debounce'
import api from '../api'
import PaymentModal from './PaymentModal.vue'
import ReportModal from './ReportModal.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const currentTab = ref('unpaid')
const sales = ref([])
const accounts = ref([])
const searchQuery = ref('')
const startDate = ref(new Date().toISOString().split('T')[0])
const endDate = ref(new Date().toISOString().split('T')[0])

const showPaymentModal = ref(false)
const selectedSale = ref(null)
const showReportModal = ref(false)
const paymentReport = ref(null)

const toast = ref({ visible: false, message: '' })

const showToast = (msg, duration = 3200) => {
  toast.value = { visible: true, message: msg }
  setTimeout(() => (toast.value.visible = false), duration)
}

const fetchSales = async () => {
  try {
    const params = {
      search: searchQuery.value.trim() || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined
    }
    const res = await api.get('/sales/', { params })
    sales.value = res.data
  } catch (err) {
    console.error('Failed to load sales:', err)
    showToast('❌ Error loading sales', 4000)
  }
}

const debouncedFetchSales = debounce(fetchSales, 420)

const fetchAccounts = async () => {
  try {
    const res = await api.get('/accounts/cash-bank')
    accounts.value = res.data
  } catch (err) {
    console.error(err)
  }
}

const filteredSales = computed(() => {
  return sales.value.filter(s =>
    currentTab.value === 'paid' ? s.balance <= 0 : s.balance > 0
  )
})

const totalAmount = computed(() =>
  filteredSales.value.reduce((sum, s) => sum + Number(s.total_amount || 0), 0)
)
const totalPaid = computed(() =>
  filteredSales.value.reduce((sum, s) => sum + Number(s.total_paid || 0), 0)
)
const totalBalance = computed(() =>
  filteredSales.value.reduce((sum, s) => sum + Number(s.balance || 0), 0)
)

const formatDate = dateStr => dateStr ? new Date(dateStr).toLocaleDateString('en-GB') : '—'
const formatCurrency = val =>
  Number(val || 0).toLocaleString('en-UG', { style: 'currency', currency: 'UGX', minimumFractionDigits: 0 })

const activeTabClass = 'px-5 py-2 rounded-lg bg-indigo-600 text-white font-medium shadow-sm transition hover:bg-indigo-700'
const inactiveTabClass = 'px-5 py-2 rounded-lg bg-white border border-gray-300 text-gray-700 font-medium transition hover:bg-gray-100'

const openPaymentModal = sale => {
  selectedSale.value = sale
  showPaymentModal.value = true
}

const previewPaymentReport = async saleId => {
  try {
    const res = await api.get(`/payments/details?sale_id=${saleId}&type=invoice`)
    paymentReport.value = res.data
    showReportModal.value = true
  } catch (err) {
    console.error(err)
    showToast('❌ Could not load report', 4000)
  }
}

const confirmDeleteSale = sale => {
  if (!confirm(`Delete sale ${sale.sale_number || sale.sale_id}?\nThis will reverse inventory & accounting entries.`))
    return

  api.delete(`/sales/${sale.sale_id}/delete`)
    .then(() => {
      showToast(`✅ Sale ${sale.sale_number || sale.sale_id} deleted successfully`)
      fetchSales()
    })
    .catch(err => {
      console.error(err)
      showToast(`❌ Delete failed: ${err.response?.data?.error || 'Server error'}`, 5000)
    })
}

onMounted(() => {
  fetchSales()
  fetchAccounts()
})
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.4s ease-out forwards;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>