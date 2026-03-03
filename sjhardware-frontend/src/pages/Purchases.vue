<template>
  <div class="p-6 max-w-7xl mx-auto bg-white shadow-lg rounded-lg">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">
      {{ isEditMode ? `Edit Purchase Order #${poId}` : 'Create Purchase Order' }}
    </h1>

    <!-- Purchase Order Header -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <!-- Supplier -->
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
        ></v-autocomplete>
        <p v-if="errors.supplier" class="text-red-500 text-sm mt-1">{{ errors.supplier }}</p>
      </div>

      <!-- Invoice Number -->
      <div>
        <label class="block font-semibold mb-1">Invoice Number *</label>
        <input
          type="text"
          v-model.trim="poHeader.invoice_number"
          placeholder="e.g. INV-2025-001"
          class="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500"
        />
        <p v-if="errors.invoice_number" class="text-red-500 text-sm mt-1">{{ errors.invoice_number }}</p>
      </div>

      <!-- Purchase Date -->
      <div>
        <label class="block font-semibold mb-1">Purchase Date</label>
        <input
          type="date"
          v-model="poHeader.purchase_date"
          class="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <!-- Memo -->
      <div>
        <label class="block font-semibold mb-1">Memo / Note</label>
        <input
          type="text"
          v-model="poHeader.memo"
          placeholder="Optional"
          class="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>

    <!-- Items Table -->
    <div class="bg-white rounded-xl shadow overflow-hidden mb-8">
      <table class="w-full">
        <thead class="bg-gradient-to-r from-indigo-100 to-purple-100 text-gray-700">
          <tr>
            <th class="p-4 text-left">Product</th>
            <th class="p-4 text-center">Current Stock</th>
            <th class="p-4 text-center">Unit</th>
            <th class="p-4 text-center">Last Purchase Price</th>
            <th class="p-4 text-center">Cost Price (UGX)</th>
            <th class="p-4 text-center">Quantity</th>
            <th class="p-4 text-center">Total (UGX)</th>
            <th class="p-4 text-center">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in poItems" :key="idx" class="hover:bg-indigo-50 transition border-b">
            <!-- Product -->
            <td class="p-4">
              <div class="space-y-3">
                <v-autocomplete
                  v-model="item.selectedProductObj"
                  :items="item.searchResults"
                  item-title="name"
                  item-value="id"
                  placeholder="Search product..."
                  variant="outlined"
                  density="comfortable"
                  clearable
                  hide-details
                  :loading="item.loading"
                  @update:search="val => debouncedSearchProduct(val, idx)"
                  @update:model-value="id => selectProduct(id, idx)"
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props">
                      <template v-slot:title>{{ item.raw.name }}</template>
                      <template v-slot:subtitle>Stock: {{ item.raw.quantity.toFixed(2) }} base units</template>
                    </v-list-item>
                  </template>
                </v-autocomplete>

                <!-- Selected Product Badge (Very Visible) -->
                <div
                  v-if="item.product_name"
                  class="bg-green-50 border border-green-200 px-4 py-2.5 rounded-lg text-base font-medium text-green-800 flex justify-between items-center shadow-sm"
                >
                  <span>Selected: <strong>{{ item.product_name }}</strong></span>
                  <span class="text-sm text-gray-600">Stock: {{ item.stock_base?.toFixed(2) || '0' }} base</span>
                </div>
              </div>
            </td>

            <!-- Current Stock (in selected unit) -->
            <td class="p-4 text-center font-medium">
              <div class="space-y-1">
                <span>{{ item.stock_in_unit ? item.stock_in_unit.toFixed(3) : '0.000' }}</span>
                <div v-if="item.unit_id" class="text-xs text-gray-500">
                  {{ selectedUnitName(idx) || 'base' }}
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
                  :disabled="!item.product_id"
                  @update:model-value="() => updateUnitAndLastPrice(idx)"
                ></v-select>

                <!-- Selected Unit Badge (Very Visible) -->
                <div
                  v-if="item.unit_id && selectedUnitName(idx)"
                  class="bg-indigo-50 border border-indigo-200 px-4 py-2 rounded-lg text-base font-medium text-indigo-800 text-center shadow-sm"
                >
                  Selected: <strong>{{ selectedUnitName(idx) }}</strong>
                </div>
              </div>
            </td>

            <!-- Last Purchase Price (Reference) -->
            <td class="p-4 text-center font-medium text-gray-600">
              {{ formatPrice(item.last_purchase_price || 0) }}
            </td>

            <!-- Editable Cost Price -->
            <td class="p-4">
              <input
                type="number"
                v-model.number="item.cost_price"
                @input="calculateTotalFromPrice(idx)"
                min="0"
                step="100"
                placeholder="0"
                class="w-full text-right border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 font-semibold text-green-700"
              />
            </td>

            <!-- Quantity -->
            <td class="p-4">
              <input
                type="number"
                v-model.number="item.quantity"
                @input="calculateTotalFromPrice(idx)"
                min="0"
                step="0.01"
                placeholder="0"
                class="w-full text-center border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500"
              />
            </td>

            <!-- Editable Total -->
            <td class="p-4">
              <input
                type="number"
                v-model.number="item.total_price"
                @input="calculatePriceFromTotal(idx)"
                min="0"
                step="100"
                placeholder="0"
                class="w-full text-right border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 font-bold text-indigo-700 text-lg"
              />
            </td>

            <!-- Remove -->
            <td class="p-4 text-center">
              <button
                @click="removeRow(idx)"
                class="w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition shadow"
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
          class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-lg transition transform hover:scale-105"
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

    <!-- Save Button -->
    <div class="text-right mb-8">
      <button
        @click="savePurchaseOrder"
        :disabled="saving"
        class="px-10 py-4 bg-green-600 hover:bg-green-700 text-white text-xl font-bold rounded-2xl shadow-2xl transition transform hover:scale-105 disabled:opacity-50"
      >
        {{ saving ? 'Saving...' : 'Save Purchase Order' }}
      </button>
    </div>

    <!-- Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="4000"
      location="top right"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import debounce from 'lodash.debounce'
import api from '../api'

const router = useRouter()

// Header
const poHeader = ref({
  supplier_id: null,
  invoice_number: '',
  purchase_date: new Date().toISOString().slice(0, 10),
  memo: ''
})

// Items
const poItems = ref([])

// Data
const suppliers = ref([])
const loadingSuppliers = ref(false)
const saving = ref(false)
const errors = ref({})
const snackbar = ref({ show: false, message: '', color: 'success' })

// Grand Total
const grandTotal = computed(() => {
  return poItems.value.reduce((sum, item) => sum + (item.total_price || 0), 0)
})

// Format Price
const formatPrice = (val) => {
  const value = Number(val) || 0
  return new Intl.NumberFormat('en-UG', { minimumFractionDigits: 0 }).format(value)
}

// Fetch Suppliers
const fetchSuppliers = async () => {
  loadingSuppliers.value = true
  try {
    const res = await api.get('/suppliers/')
    suppliers.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loadingSuppliers.value = false
  }
}

// Product Search
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
  } catch (err) {
    console.error(err)
  } finally {
    item.loading = false
  }
}, 300)

// Select Product
const selectProduct = (id, idx) => {
  const item = poItems.value[idx]
  const product = item.searchResults.find(p => p.id === id)
  if (!product) {
    item.product_id = null
    item.product_name = ''
    item.units = []
    item.unit_id = null
    item.stock_in_unit = 0
    item.cost_price = 0
    item.last_purchase_price = 0
    item.quantity = 0
    item.total_price = 0
    return
  }

  item.product_id = product.id
  item.selectedProductObj = product
  item.product_name = product.name
  item.units = product.units || []
  item.unit_id = null
  item.stock_base = product.quantity
  item.stock_in_unit = product.quantity || 0
  item.cost_price = 0
  item.last_purchase_price = 0
  item.quantity = 0
  item.total_price = 0

  item.searchResults = []
}

// Selected Unit Name (for display)
const selectedUnitName = (idx) => {
  const item = poItems.value[idx]
  const unit = item.units.find(u => u.id === item.unit_id)
  return unit ? unit.unit_name : null
}

// Update unit, stock, and last purchase price
const updateUnitAndLastPrice = (idx) => {
  const item = poItems.value[idx]
  const selectedUnit = item.units.find(u => u.id === item.unit_id)
  if (selectedUnit) {
    // Stock in selected unit
    item.stock_in_unit = item.stock_base / selectedUnit.conversion_quantity || 0

    // Last purchase price (reference)
    item.last_purchase_price = selectedUnit.last_purchase_price || selectedUnit.purchase_price || 0

    // Optional: auto-fill cost price with last purchase price (uncomment if wanted)
    // item.cost_price = item.last_purchase_price
  } else {
    item.stock_in_unit = 0
    item.last_purchase_price = 0
  }
  calculateTotalFromPrice(idx)
}

// Calculate total from cost price × quantity
const calculateTotalFromPrice = (idx) => {
  const item = poItems.value[idx]
  item.total_price = (item.quantity || 0) * (item.cost_price || 0)
}

// When total is entered, calculate cost price
const calculatePriceFromTotal = (idx) => {
  const item = poItems.value[idx]
  if (item.quantity > 0 && item.total_price > 0) {
    item.cost_price = item.total_price / item.quantity
  }
}

// Add row
const addRow = () => {
  poItems.value.push({
    product_id: null,
    product_name: '',
    units: [],
    unit_id: null,
    stock_base: 0,
    stock_in_unit: 0,
    cost_price: 0,
    last_purchase_price: 0,
    quantity: 0,
    total_price: 0,
    searchResults: [],
    selectedProductObj: null,
    loading: false
  })
}

// Remove row
const removeRow = (idx) => poItems.value.splice(idx, 1)

// Save PO
const savePurchaseOrder = async () => {
  errors.value = {}

  if (!poHeader.value.supplier_id) {
    errors.value.supplier = 'Select a supplier'
    return
  }
  if (!poHeader.value.invoice_number.trim()) {
    errors.value.invoice_number = 'Invoice number required'
    return
  }

  const validItems = poItems.value.filter(i => i.product_id && i.unit_id && i.quantity > 0 && i.cost_price > 0)
  if (validItems.length === 0) {
    alert('Add at least one valid item with quantity and cost price')
    return
  }

  const payload = {
    supplier_id: poHeader.value.supplier_id,
    invoice_number: poHeader.value.invoice_number.trim(),
    purchase_date: poHeader.value.purchase_date,
    memo: poHeader.value.memo || '',
    items: validItems.map(i => ({
      product_id: i.product_id,
      unit_id: i.unit_id,
      quantity: i.quantity,
      unit_price: i.cost_price
    }))
  }

  saving.value = true
  try {
    const res = await api.post('/suppliers/orders', payload)
    snackbar.value = {
      show: true,
      message: 'Purchase Order saved successfully!',
      color: 'success'
    }
    // Reset form
    poHeader.value = {
      supplier_id: null,
      invoice_number: '',
      purchase_date: new Date().toISOString().slice(0, 10),
      memo: ''
    }
    poItems.value = []
    addRow()
  } catch (err) {
    snackbar.value = {
      show: true,
      message: err.response?.data?.error || 'Failed to save PO',
      color: 'error'
    }
  } finally {
    saving.value = false
  }
}

// Init
onMounted(() => {
  fetchSuppliers()
  addRow()
})
</script>

<style scoped>
/* Optional: Enhance selected badges */
.bg-green-50 {
  background-color: #f0fdf4;
}
.bg-indigo-50 {
  background-color: #eef2ff;
}
</style>