<!-- src/views/reports/CustomerPaymentsReport.vue -->
<template>
    <div class="p-6 max-w-7xl mx-auto space-y-8">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
        <h1 class="text-3xl font-bold text-black-900 dark:text-black tracking-tight">
          Customer Payments Report
        </h1>
        <button
          @click="resetFilters"
          class="px-5 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 
                 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg text-sm font-medium text-black-700 
                 dark:text-black-300 transition shadow-sm"
        >
          Reset Filters
        </button>
      </div>
  
      <!-- Filters Card -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <!-- Customer -->
          <div>
            <label class="block text-sm font-medium text-black-700 dark:text-black-300 mb-1.5">Customer</label>
            <v-autocomplete
              v-model="selectedCustomerId"
              :items="customers"
              item-title="name"
              item-value="id"
              placeholder="All customers"
              variant="outlined"
              density="comfortable"
              clearable
              :loading="loadingCustomers"
              @update:model-value="fetchReport"
              class="rounded-lg"
            ></v-autocomplete>
          </div>
  
          <!-- Start Date -->
          <div>
            <label class="block text-sm font-medium text-black-700 dark:text-black-300 mb-1.5">From Date</label>
            <input
              type="date"
              v-model="startDate"
              @change="fetchReport"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg 
                     focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 
                     dark:bg-gray-700 dark:text-black-100 transition"
            />
          </div>
  
          <!-- End Date -->
          <div>
            <label class="block text-sm font-medium text-black-700 dark:text-black-300 mb-1.5">To Date</label>
            <input
              type="date"
              v-model="endDate"
              @change="fetchReport"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg 
                     focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 
                     dark:bg-gray-700 dark:text-black-100 transition"
            />
          </div>
  
          <!-- Quick Range -->
          <div class="flex items-end">
            <select
              v-model="quickRange"
              @change="applyQuickRange"
              class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg 
                     focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 
                     dark:bg-gray-700 dark:text-black-100 transition"
            >
              <option value="">Custom Range</option>
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="this-week">This Week</option>
              <option value="last-7-days">Last 7 Days</option>
              <option value="this-month">This Month</option>
              <option value="last-30-days">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>
  
      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <div class="animate-spin rounded-full h-14 w-14 border-4 border-indigo-500 border-t-transparent"></div>
        <p class="mt-6 text-lg text-black-600 dark:text-black-400">Loading customer payments...</p>
      </div>
  
      <!-- No Data -->
      <div v-else-if="!loading && !hasData" class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
        <h3 class="text-xl font-semibold text-black-700 dark:text-black-300 mb-3">
          No payments found
        </h3>
        <p class="text-black-600 dark:text-black-400">
          Try adjusting the date range or selecting a different customer.
        </p>
      </div>
  
      <!-- Summary Cards -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p class="text-sm font-medium text-black-600 dark:text-black-400">Total Received</p>
          <p class="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">
            {{ formatCurrency(totalReceived) }}
          </p>
        </div>
  
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p class="text-sm font-medium text-black-600 dark:text-black-400">Total Payments</p>
          <p class="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mt-2">
            {{ totalPayments }}
          </p>
        </div>
  
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p class="text-sm font-medium text-black-600 dark:text-black-400">Customers</p>
          <p class="text-3xl font-bold text-violet-600 dark:text-violet-400 mt-2">
            {{ customersData.length }}
          </p>
        </div>
      </div>
  
      <!-- Customer Cards -->
      <div v-if="!loading && hasData" class="space-y-6">
        <div
          v-for="customer in customersData"
          :key="customer.id"
          class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
          <!-- Customer Header -->
          <div
            @click="toggleCustomer(customer.id)"
            class="px-6 py-5 flex justify-between items-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
          >
            <div>
              <h3 class="text-xl font-semibold text-black-900 dark:text-black">
                {{ customer.name }}
              </h3>
              <p class="text-sm text-black-600 dark:text-black-400 mt-1">
                {{ customer.phone || 'No phone' }} • {{ customer.email || 'No email' }}
              </p>
            </div>
            <div class="text-right">
              <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {{ formatCurrency(customer.total_paid) }}
              </p>
              <p class="text-sm text-black-500 dark:text-black-400 mt-1">
                {{ customer.payments.length }} payment{{ customer.payments.length !== 1 ? 's' : '' }}
              </p>
            </div>
          </div>
  
          <!-- Payments Table -->
          <div v-if="expandedCustomers[customer.id]" class="border-t border-black-200 dark:border-gray-700">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-900/50">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Date</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Sale #</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Amount</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Method</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Reference</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Sale Total</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-black-600 dark:text-black-300 uppercase tracking-wider">Balance</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                  <tr
                    v-for="payment in customer.payments"
                    :key="payment.payment_id"
                    class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition"
                  >
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-black-900 dark:text-black-200">
                      {{ formatDate(payment.payment_date) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                      <router-link
                        :to="`/sales/${payment.sale_id}`"
                        class="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
                      >
                        {{ payment.sale_number || '—' }}
                      </router-link>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                      {{ formatCurrency(payment.amount) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-black-700 dark:text-black-300">
                      {{ payment.payment_type }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-black-600 dark:text-black-400">
                      {{ payment.reference || '—' }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-black-900 dark:text-black-200">
                      {{ formatCurrency(payment.sale_total) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-amber-600 dark:text-amber-400">
                      {{ formatCurrency(payment.sale_balance) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import api from '@/api'
  
  const router = useRouter()
  
  const customers = ref([])
  const loadingCustomers = ref(false)
  const selectedCustomerId = ref(null)
  
  const startDate = ref('')
  const endDate = ref('')
  const quickRange = ref('')
  
  const customersData = ref([])
  const totalReceived = ref(0)
  const totalPayments = ref(0)
  const loading = ref(false)
  const expandedCustomers = ref({})
  
  const hasData = computed(() => customersData.value.length > 0)
  
  // Formatters
  const formatCurrency = (val) => {
    return Number(val || 0).toLocaleString('en-UG', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    })
  }
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    }) + ', ' + date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  // Fetch customers
  const fetchCustomers = async () => {
    loadingCustomers.value = true
    try {
      const res = await api.get('/customer/')
      customers.value = res.data || []
    } catch (err) {
      console.error('Failed to load customers:', err)
    } finally {
      loadingCustomers.value = false
    }
  }
  
  // Fetch report
  const fetchReport = async () => {
    loading.value = true
    try {
      const params = {}
      if (startDate.value) params.start_date = startDate.value
      if (endDate.value) params.end_date = endDate.value
      if (selectedCustomerId.value) params.customer_id = selectedCustomerId.value
  
      const res = await api.get('/reports/customer-payments', { params })
  
      customersData.value = res.data.customers || []
      totalReceived.value = res.data.total_received || 0
  
      totalPayments.value = customersData.value.reduce(
        (sum, c) => sum + (c.payments?.length || 0), 0
      )
  
      // Auto-expand single customer
      if (customersData.value.length === 1) {
        expandedCustomers.value[customersData.value[0].id] = true
      }
    } catch (err) {
      console.error('Report fetch failed:', err)
      customersData.value = []
    } finally {
      loading.value = false
    }
  }
  
  const toggleCustomer = (id) => {
    expandedCustomers.value[id] = !expandedCustomers.value[id]
  }
  
  const applyQuickRange = () => {
    const today = new Date()
    let start = ''
    let end = today.toISOString().split('T')[0]
  
    switch (quickRange.value) {
      case 'today':
        start = end
        break
      case 'yesterday':
        const yest = new Date(today)
        yest.setDate(today.getDate() - 1)
        start = end = yest.toISOString().split('T')[0]
        break
      case 'this-week':
        const first = new Date(today)
        first.setDate(today.getDate() - today.getDay())
        start = first.toISOString().split('T')[0]
        break
      case 'last-7-days':
        const last7 = new Date(today)
        last7.setDate(today.getDate() - 7)
        start = last7.toISOString().split('T')[0]
        break
      case 'this-month':
        start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
        break
      case 'last-30-days':
        const last30 = new Date(today)
        last30.setDate(today.getDate() - 30)
        start = last30.toISOString().split('T')[0]
        break
    }
  
    startDate.value = start
    endDate.value = end
    fetchReport()
  }
  
  const resetFilters = () => {
    selectedCustomerId.value = null
    startDate.value = ''
    endDate.value = ''
    quickRange.value = ''
    fetchReport()
  }
  
  onMounted(async () => {
    await fetchCustomers()
    fetchReport()
  })
  </script>
  
  <style scoped>
  /* Fade-in animation */
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .animate-fadeIn {
    animation: fadeIn 0.6s ease-out forwards;
  }
  
  /* Smooth hover transitions */
  .hover\:bg-gray-50:hover {
    background-color: #f9fafb;
  }
  .dark .hover\:bg-gray-700\/50:hover {
    background-color: rgba(55, 65, 81, 0.5);
  }
  </style>