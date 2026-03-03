<template>
  <div class="p-6 max-w-7xl mx-auto bg-white shadow-lg rounded-lg relative">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">
      Edit Purchase Order #{{ poId }}
    </h1>

    <!-- Header -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div>
        <label class="block font-semibold mb-1">Supplier *</label>
        <v-autocomplete
          v-model="poHeader.supplier_id"
          :items="suppliers"
          item-title="name"
          item-value="id"
          placeholder="Select supplier"
          variant="outlined"
          density="comfortable"
          clearable
          :loading="loadingSuppliers"
          :disabled="isFormLocked"
        ></v-autocomplete>
      </div>

      <div>
        <label class="block font-semibold mb-1">Invoice Number *</label>
        <input
          type="text"
          v-model.trim="poHeader.invoice_number"
          class="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500"
          :disabled="isFormLocked"
        />
      </div>

      <div>
        <label class="block font-semibold mb-1">Purchase Date</label>
        <input
          type="date"
          v-model="poHeader.purchase_date"
          class="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500"
          :disabled="isFormLocked"
        />
      </div>

      <div>
        <label class="block font-semibold mb-1">Memo / Note</label>
        <input
          type="text"
          v-model="poHeader.memo"
          class="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500"
          :disabled="isFormLocked"
        />
      </div>
    </div>

    <!-- Items Table -->
    <div class="bg-white rounded-xl shadow overflow-hidden mb-8 relative">
      <table class="w-full">
        <thead class="bg-gradient-to-r from-indigo-100 to-purple-100 text-gray-700">
          <tr>
            <th class="p-4 text-left">Product</th>
            <th class="p-4 text-center">Current Stock</th>
            <th class="p-4 text-center">Unit</th>
            <th class="p-4 text-center">Cost Price (UGX)</th>
            <th class="p-4 text-center">Quantity</th>
            <th class="p-4 text-center">Total (UGX)</th>
            <th class="p-4 text-center">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in poItems" :key="item.id || idx" class="hover:bg-indigo-50 transition border-b">
            <!-- Product -->
            <td class="p-4">
              <div class="space-y-3">
                <v-autocomplete
                  v-model="item.selectedProductObj"
                  :items="item.searchResults"
                  item-title="name"
                  item-value="id"
                  placeholder="Search or change product..."
                  variant="outlined"
                  density="comfortable"
                  clearable
                  hide-details
                  :loading="item.loading"
                  :disabled="isFormLocked"
                  @update:search="val => debouncedSearchProduct(val, idx)"
                  @update:model-value="id => selectProduct(id, idx)"
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props">
                      <template v-slot:title>{{ item.raw.name }}</template>
                      <template v-slot:subtitle>Stock: {{ item.raw.quantity.toFixed(2) }} base units</template>
                    </v-list-item>
                  </template>

                  <template v-slot:selection="{ item }">
                    <span class="font-medium text-indigo-700">{{ item.name }}</span>
                  </template>
                </v-autocomplete>

                <!-- Selected Product – Clear & Beautiful Badge -->
                <div
                  v-if="item.product_name"
                  class="bg-green-50 border border-green-200 px-4 py-3 rounded-lg text-base font-medium text-green-800 shadow-sm flex justify-between items-center"
                >
                  <span>Selected: <strong>{{ item.product_name }}</strong></span>
                  <span class="text-sm text-gray-600">Stock: {{ item.stock_base?.toFixed(2) || '0' }} base</span>
                </div>
              </div>
            </td>

            <!-- Current Stock (in selected unit) -->
            <td class="p-4 text-center font-medium">
              <div class="space-y-1">
                <span class="text-lg">{{ item.stock_in_unit ? item.stock_in_unit.toFixed(3) : '0.000' }}</span>
                <div v-if="item.unit_id" class="text-xs text-gray-500">
                  {{ selectedUnitName(idx) || 'base units' }}
                </div>
              </div>
            </td>

            <!-- Unit -->
            <td class="p-4">
              <div class="space-y-3">
                <v-select
                  v-model="item.unit_id"
                  :items="item.units"
                  item-title="unit_name"
                  item-value="id"
                  placeholder="Select unit"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  :disabled="isFormLocked || !item.product_id"
                  @update:model-value="() => updateUnitStock(idx)"
                ></v-select>

                <!-- Selected Unit – Clear & Beautiful Badge -->
                <div
                  v-if="item.unit_id && selectedUnitName(idx)"
                  class="bg-indigo-50 border border-indigo-200 px-4 py-3 rounded-lg text-base font-medium text-indigo-800 text-center shadow-sm"
                >
                  Selected Unit: <strong>{{ selectedUnitName(idx) }}</strong>
                </div>
              </div>
            </td>

            <!-- Cost Price -->
            <td class="p-4">
              <input
                type="number"
                v-model.number="item.cost_price"
                @input="calculateTotalFromPrice(item)"
                min="0"
                step="100"
                class="w-full text-right border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500"
                :disabled="isFormLocked"
              />
            </td>

            <!-- Quantity -->
            <td class="p-4">
              <input
                type="number"
                v-model.number="item.quantity"
                @input="calculateTotalFromPrice(item)"
                min="0"
                step="0.01"
                class="w-full text-center border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500"
                :disabled="isFormLocked"
              />
            </td>

            <!-- Editable Total Price -->
            <td class="p-4">
              <input
                type="number"
                v-model.number="item.total_price"
                @input="calculatePriceFromTotal(item)"
                min="0"
                step="100"
                class="w-full text-right border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 bg-yellow-50"
                :disabled="isFormLocked"
              />
            </td>

            <!-- Remove -->
            <td class="p-4 text-center">
              <button
                @click="removeRow(idx)"
                :disabled="isFormLocked"
                class="w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition shadow disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ✕
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Add Row + Grand Total -->
      <div class="p-6 bg-gradient-to-r from-indigo-50 to-purple-50 flex justify-between items-center">
        <button
          @click="addRow"
          :disabled="isFormLocked"
          class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          + Add Product
        </button>

        <div class="text-right">
          <div class="text-2xl font-bold text-gray-800">
            Grand Total: <span class="text-indigo-700">{{ formatPrice(grandTotal) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Update Button -->
    <div class="text-right mb-8">
      <button
        @click="updatePurchaseOrder"
        :disabled="saving"
        class="px-10 py-4 bg-green-600 hover:bg-green-700 text-white text-xl font-bold rounded-2xl shadow-2xl transition disabled:opacity-70"
      >
        {{ saving ? 'Saving & Redirecting...' : 'Update Purchase Order' }}
      </button>
    </div>

    <!-- Blocking Overlay during save + redirect -->
    <div
      v-if="saving"
      class="absolute inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 rounded-lg"
    >
      <div class="bg-white p-8 rounded-xl shadow-2xl text-center max-w-md">
        <v-progress-circular
          indeterminate
          size="64"
          color="indigo"
          class="mb-6"
        ></v-progress-circular>
        <h3 class="text-xl font-bold text-gray-800 mb-2">Saving Purchase Order</h3>
        <p class="text-gray-600">
          Please wait... Do not close or refresh the page.<br>
          Redirecting after successful save...
        </p>
      </div>
    </div>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="5000" location="top right">
      {{ snackbar.message }}
    </v-snackbar>

    <!-- Loading (initial) -->
    <div v-if="!loaded" class="text-center py-20">
      <v-progress-circular indeterminate size="64" color="indigo"></v-progress-circular>
      <p class="mt-4 text-gray-600">Loading purchase order data...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import debounce from 'lodash.debounce'
import api from '../api'

const route = useRoute()
const router = useRouter()
const poId = route.params.id

const poHeader = ref({
  supplier_id: null,
  invoice_number: '',
  purchase_date: '',
  memo: ''
})

const poItems = ref([])
const suppliers = ref([])
const loadingSuppliers = ref(false)
const saving = ref(false)
const loaded = ref(false)
const snackbar = ref({ show: false, message: '', color: 'success' })

const isFormLocked = computed(() => saving.value)

const grandTotal = computed(() => poItems.value.reduce((sum, i) => sum + (i.total_price || 0), 0))

const formatPrice = (val) => new Intl.NumberFormat('en-UG', { minimumFractionDigits: 0 }).format(Number(val) || 0)

const getUnitName = (item) => {
  if (!item.unit_id || !item.units.length) return '—'
  const u = item.units.find(unit => unit.id === item.unit_id)
  return u ? u.unit_name : '—'
}

// Helper to show selected unit name clearly
const selectedUnitName = (idx) => {
  const item = poItems.value[idx]
  const unit = item.units.find(u => u.id === item.unit_id)
  return unit ? unit.unit_name : null
}

const fetchSuppliers = async () => {
  loadingSuppliers.value = true
  try {
    const res = await api.get('/suppliers/')
    suppliers.value = Array.isArray(res.data) ? res.data : res.data.data || []
  } catch (err) {
    console.error(err)
  } finally {
    loadingSuppliers.value = false
  }
}

const debouncedSearchProduct = debounce(async (query, idx) => {
  const item = poItems.value[idx]
  if (!query || query.trim().length < 2) {
    item.searchResults = []
    return
  }
  item.loading = true
  try {
    const res = await api.get('/inventory/products/search', { params: { name: query } })
    item.searchResults = res.data
  } finally {
    item.loading = false
  }
}, 300)

const selectProduct = (id, idx) => {
  const item = poItems.value[idx]

  if (!id) {
    item.product_id = null
    item.product_name = ''
    item.units = []
    item.unit_id = null
    item.stock_base = 0
    item.stock_in_unit = 0
    item.selectedProductObj = null
    item.searchResults = []
    calculateTotalFromPrice(item)
    return
  }

  const product = item.searchResults.find(p => p.id === id)
  if (!product) return

  item.product_id = product.id
  item.product_name = product.name
  item.units = product.units || []
  item.stock_base = product.quantity || 0
  item.selectedProductObj = product

  if (item.unit_id && !item.units.some(u => u.id === item.unit_id)) {
    item.unit_id = null
  }

  updateUnitStock(idx)
  item.searchResults = []
}

const updateUnitStock = (idx) => {
  const item = poItems.value[idx]
  const selectedUnit = item.units.find(u => u.id === item.unit_id)

  if (selectedUnit && selectedUnit.conversion_quantity > 0) {
    item.stock_in_unit = (item.stock_base || 0) / selectedUnit.conversion_quantity
  } else {
    item.stock_in_unit = item.stock_base || 0
  }
  calculateTotalFromPrice(item)
}

const calculateTotalFromPrice = (item) => {
  item.total_price = (item.quantity || 0) * (item.cost_price || 0)
}

const calculatePriceFromTotal = (item) => {
  if (item.quantity > 0) {
    item.cost_price = Number((item.total_price / item.quantity).toFixed(2))
  } else {
    item.cost_price = 0
  }
}

const addRow = () => {
  poItems.value.push({
    id: null,
    product_id: null,
    product_name: '',
    units: [],
    unit_id: null,
    stock_base: 0,
    stock_in_unit: 0,
    cost_price: 0,
    quantity: 0,
    total_price: 0,
    searchResults: [],
    selectedProductObj: null,
    loading: false
  })
}

const removeRow = (idx) => poItems.value.splice(idx, 1)

const fetchPurchaseOrder = async () => {
  try {
    const res = await api.get(`/suppliers/orders/${poId}`)
    const data = res.data

    poHeader.value = {
      supplier_id: data.supplier_id,
      invoice_number: data.invoice_number || '',
      purchase_date: data.purchase_date?.split('T')[0] || '',
      memo: data.memo || ''
    }

    const items = []

    for (const i of data.items) {
      let units = []
      let stock_base = 0
      let selectedProductObj = null

      try {
        const prodRes = await api.get(`/inventory/products/${i.product_id}`)
        const prod = prodRes.data
        units = prod.units || []
        stock_base = prod.quantity || 0
        selectedProductObj = { id: prod.id, name: prod.name, quantity: prod.quantity }
      } catch (err) {
        console.warn(`Cannot fetch fresh data for product ${i.product_id}`)
        selectedProductObj = { id: i.product_id, name: i.product_name || 'Unknown' }
      }

      if (units.length === 0 && i.unit_id) {
        units = [{
          id: i.unit_id,
          unit_name: i.unit_name || 'Unknown Unit',
          conversion_quantity: 1
        }]
      }

      const newItem = {
        id: i.id,
        product_id: i.product_id,
        product_name: i.product_name || 'Unknown Product',
        units,
        unit_id: i.unit_id,
        stock_base,
        stock_in_unit: 0,
        cost_price: i.unit_price || 0,
        quantity: i.quantity || 0,
        total_price: (i.quantity || 0) * (i.unit_price || 0),
        searchResults: [],
        selectedProductObj,
        loading: false
      }

      items.push(newItem)
    }

    poItems.value = items
    await nextTick()
    poItems.value.forEach((_, idx) => updateUnitStock(idx))

    loaded.value = true
  } catch (err) {
    console.error(err)
    snackbar.value = { show: true, message: 'Failed to load purchase order', color: 'error' }
    loaded.value = true
  }
}

const updatePurchaseOrder = async () => {
  const validItems = poItems.value.filter(i => i.product_id && i.unit_id && i.quantity > 0 && i.cost_price >= 0)
  if (validItems.length === 0) {
    snackbar.value = { show: true, message: 'Add at least one valid item', color: 'error' }
    return
  }

  const payload = {
    supplier_id: poHeader.value.supplier_id,
    invoice_number: poHeader.value.invoice_number.trim(),
    purchase_date: poHeader.value.purchase_date || null,
    memo: poHeader.value.memo || '',
    items: validItems.map(i => ({
      id: i.id || undefined,
      product_id: i.product_id,
      unit_id: i.unit_id,
      quantity: i.quantity,
      unit_price: Number(i.cost_price.toFixed(2))
    }))
  }

  saving.value = true

  try {
    await api.put(`/suppliers/orders/${poId}/edit`, payload)
    snackbar.value = { 
      show: true, 
      message: 'Purchase Order updated successfully! Redirecting...', 
      color: 'success' 
    }

    await new Promise(resolve => setTimeout(resolve, 1800))
    router.push('/purchaselist')
  } catch (err) {
    snackbar.value = { 
      show: true, 
      message: err.response?.data?.error || 'Update failed', 
      color: 'error' 
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await fetchSuppliers()
  await fetchPurchaseOrder()
  if (poItems.value.length === 0) addRow()
})
</script>

<style scoped>
/* Highlight editable total price */
input[type="number"][v-model*="total_price"] {
  background-color: #fefce8 !important;
}

/* Make selected badges pop more */
.bg-green-50 {
  background-color: #f0fdf4 !important;
}
.bg-indigo-50 {
  background-color: #eef2ff !important;
}

/* Stronger disabled look */
:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
</style>