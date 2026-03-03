<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-semibold mb-6 text-gray-800">📦 Inventory Management</h1>

    <!-- Tabs -->
    <div class="mb-6 flex gap-3 border-b pb-2">
      <button @click="activeTab = 'products'" :class="tabClass('products')">
        Products ({{ products.length }})
      </button>
      <button @click="activeTab = 'categories'" :class="tabClass('categories')">
        Categories ({{ categories.length }})
      </button>
    </div>

    <!-- ================ PRODUCTS TAB ================ -->
    <div v-if="activeTab === 'products'">
      <!-- Add Product Button -->
      <button @click="openProductModal()" class="mb-4 btn-primary">
        + Add New Product
      </button>

      <!-- Search -->
      <div class="mb-6 flex gap-3">
        <input
          v-model="searchQuery"
          @input="debouncedSearch"
          placeholder="Search by name or SKU..."
          class="input flex-1"
        />
        <button @click="fetchProducts" class="btn-gray">Refresh</button>
      </div>

      <!-- Export Buttons -->
      <div class="mb-6 flex gap-3">
        <button @click="exportToExcel" class="btn-primary">Export to Excel</button>
        <button @click="exportToPDF" class="btn-primary">Export to PDF</button>
      </div>

      <!-- Products Table -->
      <div class="bg-white rounded-xl shadow overflow-hidden">
        <table class="min-w-full">
          <thead class="bg-gray-100">
            <tr>
              <th class="th">ID</th>
              <th class="th">Name</th>
              <th class="th">Description</th>
              <th class="th">SKU</th>
              <th class="th">Cost Price</th>
              <th class="th">Category</th>
              <th class="th text-center">Stock (Base Units)</th>
              <th class="th">Units & Prices</th>
              <th class="th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in displayedProducts" :key="p.id" class="hover:bg-blue-50 transition">
              <td class="td text-center">{{ p.id }}</td>
              <td class="td font-medium">{{ p.name }}</td>
              <td class="td">{{ p.description || '-' }}</td>
              <td class="td">{{ p.sku }}</td>
              <td class="td">{{formatPrice( p.cost_price )}}</td>
              <td class="td">{{ p.category_name || '-' }}</td>
              <td class="td text-center font-bold text-lg">
                <span :class="p.quantity > 10 ? 'text-green-600' : p.quantity > 0 ? 'text-orange-600' : 'text-red-600'">
                  {{ Number(p.quantity).toFixed(2) }}
                </span>
              </td>
              <td class="td">
                <div class="space-y-1">
                  <div v-for="unit in p.units" :key="unit.id" class="text-xs">
                    <span class="font-medium text-blue-700">{{ unit.unit_name }}</span>
                    <span v-if="unit.conversion_quantity !== 1" class="text-gray-600">
                      ({{ unit.conversion_quantity }}× base)
                    </span>
                    <span class="ml-2 text-green-700 font-semibold">
                      → {{ formatPrice(unit.retail_price) }}
                    </span>
                  </div>
                  <div v-if="!p.units.length" class="text-gray-400 text-xs">No units defined</div>
                </div>
              </td>
              <td class="td text-center space-x-2">
                <button @click="openProductModal(p)" class="btn-sm bg-blue-600 hover:bg-blue-700">Edit</button>
                <button @click="deleteProduct(p.id)" class="btn-sm bg-red-600 hover:bg-red-700">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ================ CATEGORIES TAB ================ -->
    <div v-if="activeTab === 'categories'" class="animate-fadeIn">
      <button @click="openCategoryModal()" class="mb-4 btn-primary">+ Add Category</button>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="cat in categories"
          :key="cat.id"
          class="bg-white p-5 rounded-xl shadow hover:shadow-lg transition"
        >
          <div class="flex justify-between items-start">
            <div>
              <h3 class="font-bold text-lg">{{ cat.name }}</h3>
              <p class="text-gray-600 text-sm mt-1">{{ cat.description || 'No description' }}</p>
            </div>
            <div class="flex gap-2">
              <button @click="openCategoryModal(cat)" class="text-blue-600 hover:text-blue-800">Edit</button>
              <button @click="deleteCategory(cat.id)" class="text-red-600 hover:text-red-800">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ================ PRODUCT MODAL ================ -->
    <teleport to="body">
      <div v-if="showProductModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-screen overflow-y-auto">
          <div class="p-6 border-b">
            <h2 class="text-2xl font-bold">{{ editingProduct ? 'Edit' : 'Add New' }} Product</h2>
          </div>

          <div class="p-6 space-y-6">
            <!-- Basic Info -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1">Product Name *</label>
                <input v-model="productForm.name" placeholder="e.g. Maize Flour" class="input" required />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">SKU (Unique) *</label>
                <input v-model="productForm.sku" placeholder="e.g. MF-001" class="input" required />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Cost Price (UGX) *</label>
                <input v-model.number="productForm.cost_price" type="number" min="0" step="100" placeholder="e.g. 1000" class="input" required />
              </div>
              <div class="md:col-span-2">
                <label class="block text-sm font-medium mb-1">Description (Optional)</label>
                <textarea v-model="productForm.description" placeholder="Brief product description..." class="input h-24"></textarea>
              </div>
              <div class="md:col-span-2">
                <label class="block text-sm font-medium mb-1">Category</label>
                <select v-model="productForm.category_id" class="input">
                  <option :value="null">Select Category (Optional)</option>
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>

            <!-- Units Section -->
            <div class="border-t pt-6">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-xl font-semibold">Units & Retail Prices</h3>
                <button type="button" @click="addUnit" class="text-blue-600 font-medium hover:underline">
                  + Add Unit
                </button>
              </div>

              <div v-for="(unit, i) in productForm.units" :key="i" class="mb-5 p-5 border rounded-xl bg-gray-50">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label class="block text-xs font-medium text-gray-600">Unit Name *</label>
                    <input
                      v-model="unit.unit_name"
                      placeholder="e.g. Kilo, Sack, Quarter"
                      class="input mt-1"
                      required
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600">Conversion to Base *</label>
                    <input
                      v-model.number="unit.conversion_quantity"
                      type="number"
                      step="0.01"
                      min="0.01"
                      placeholder="e.g. 50 for 50kg sack"
                      class="input mt-1"
                      required
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600">Retail Price (UGX) *</label>
                    <input
                      v-model.number="unit.retail_price"
                      type="number"
                      min="0"
                      step="100"
                      placeholder="e.g. 150000"
                      class="input mt-1"
                      required
                    />
                  </div>
                  <div class="flex items-end">
                    <button
                      type="button"
                      @click="removeUnit(i)"
                      class="w-full px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition"
                    >
                      Remove
                    </button>
                  </div>
                </div>
                <div class="mt-2 text-sm text-gray-600">
                  → This unit = {{ unit.conversion_quantity || 1 }} × base unit | 
                  Price per unit: <strong>{{ formatPrice(unit.retail_price) }}</strong>
                </div>
              </div>

              <div v-if="!productForm.units.length" class="text-center py-10 text-gray-500 border-2 border-dashed rounded-xl">
                <p class="text-lg">No units added yet</p>
                <p class="text-sm mt-2">Click "+ Add Unit" to define how this product is sold</p>
              </div>
            </div>
          </div>

          <div class="p-6 border-t flex justify-end gap-3">
            <button @click="closeProductModal" class="btn-secondary">Cancel</button>
            <button @click="saveProduct" :disabled="saving || !productForm.units.length" class="btn-primary">
              {{ saving ? 'Saving...' : 'Save Product' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- ================ CATEGORY MODAL ================ -->
    <teleport to="body">
      <div v-if="showCategoryModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
          <div class="p-6 border-b">
            <h2 class="text-2xl font-bold">{{ editingCategory ? 'Edit' : 'Add' }} Category</h2>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">Category Name *</label>
              <input v-model="categoryForm.name" placeholder="e.g. Grains" class="input w-full" required />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Description (Optional)</label>
              <textarea v-model="categoryForm.description" placeholder="Brief description..." class="input w-full h-24"></textarea>
            </div>
          </div>
          <div class="p-6 border-t flex justify-end gap-3">
            <button @click="showCategoryModal = false" class="btn-secondary">Cancel</button>
            <button @click="saveCategory" class="btn-primary">Save Category</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Notification -->
    <div v-if="notification" class="fixed bottom-6 right-6 bg-gray-900 text-white px-6 py-3 rounded-xl shadow-2xl z-50 animate-pulse text-sm">
      {{ notification }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import * as XLSX from 'xlsx';

const activeTab = ref('products');
const products = ref([]);
const categories = ref([]);
const searchQuery = ref('');
const displayedProducts = ref([]);

const showProductModal = ref(false);
const showCategoryModal = ref(false);
const editingProduct = ref(null);
const editingCategory = ref(null);
const saving = ref(false);
const notification = ref('');

const productForm = ref({
  id: null,
  name: '',
  sku: '',
  description: '',
  cost_price: 0,
  category_id: null,
  units: []
});

const categoryForm = ref({
  id: null,
  name: '',
  description: ''
});

// Tabs
const tabClass = (tab) => {
  return `px-6 py-3 rounded-t-lg font-semibold transition ${
    activeTab.value === tab
      ? 'bg-blue-600 text-white shadow-lg'
      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
  }`;
};

// Fetch Data
const fetchProducts = async () => {
  try {
    const res = await api.get('/inventory/products');
    products.value = res.data;
    displayedProducts.value = res.data;
  } catch (err) {
    notify('Failed to load products');
  }
};

const fetchCategories = async () => {
  try {
    const res = await api.get('/inventory/categories');
    categories.value = res.data;
  } catch {
    notify('Failed to load categories');
  }
};

// Search
let searchTimeout;
const debouncedSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    const q = searchQuery.value.toLowerCase().trim();
    if (!q) {
      displayedProducts.value = products.value;
      return;
    }
    displayedProducts.value = products.value.filter(p =>
      p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)
    );
  }, 300);
};

// Open edit modal
const openProductModal = async (product = null) => {
  if (product) {
    // 1. Core product data
    const coreRes = await api.get(`/inventory/products/${product.id}`);
    const core = coreRes.data;

    // 2. Units data (new endpoint)
    const unitsRes = await api.get(`/inventory/products/${product.id}/units`);
    const units = unitsRes.data;

    productForm.value = {
      id: core.id,
      name: core.name,
      sku: core.sku,
      description: core.description || '',
      cost_price: core.cost_price || 0,
      category_id: core.category_id,
      units: units.length ? units : [{ unit_name: '', conversion_quantity: 1, retail_price: 0 }]
    };
    editingProduct.value = true;
  } else {
    // new product
    productForm.value = {
      id: null,
      name: '',
      sku: '',
      description: '',
      cost_price: 0,
      category_id: null,
      units: [{ unit_name: 'Kilo', conversion_quantity: 1, retail_price: 0 }]
    };
    editingProduct.value = false;
  }
  showProductModal.value = true;
};

const closeProductModal = () => {
  showProductModal.value = false;
  editingProduct.value = null;
};

const addUnit = () => {
  productForm.value.units.push({
    unit_name: '',
    conversion_quantity: 1,
    retail_price: 0
  });
};

const removeUnit = (index) => {
  if (productForm.value.units.length > 1) {
    productForm.value.units.splice(index, 1);
  } else {
    notify('At least one unit is required');
  }
};

const saveProduct = async () => {
  // Validation
  if (!productForm.value.name.trim()) return notify('Product name is required');
  if (!productForm.value.sku.trim()) return notify('SKU is required');
  if (productForm.value.cost_price < 0) return notify('Cost price cannot be negative');
  if (productForm.value.units.some(u => !u.unit_name.trim())) return notify('All units must have a name');
  if (productForm.value.units.some(u => u.conversion_quantity <= 0)) return notify('Conversion must be > 0');
  if (productForm.value.units.some(u => u.retail_price < 0)) return notify('Price cannot be negative');

  saving.value = true;
  try {
    if (editingProduct.value) {
      await api.put(`/inventory/products/${productForm.value.id}`, productForm.value);
      notify('Product updated successfully!');
    } else {
      await api.post('/inventory/products', productForm.value);
      notify('Product added successfully!');
    }
    closeProductModal();
    fetchProducts();
  } catch (err) {
    console.error(err);
    notify('Error saving product. Check console.');
  } finally {
    saving.value = false;
  }
};

const deleteProduct = async (id) => {
  if (!confirm('Delete this product permanently?')) return;
  try {
    await api.delete(`/inventory/products/${id}`);
    notify('Product deleted');
    fetchProducts();
  } catch {
    notify('Failed to delete');
  }
};

// Export Functions
const exportToExcel = () => {
  const data = products.value.map(p => ({
    ID: p.id,
    Name: p.name,
    Description: p.description || '',
    SKU: p.sku,
    'Cost Price': p.cost_price,
    Category: p.category_name || '',
    'Stock (Base Units)': p.quantity,
    'Units & Rates': p.units.map(u => `${u.unit_name} (${u.conversion_quantity} base) - ${u.retail_price} UGX`).join('; ')
  }));

  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Products');
  XLSX.writeFile(wb, 'products_inventory.xlsx');
};

const exportToPDF = () => {
  const doc = new jsPDF();
  doc.setFontSize(18);
  doc.text('Products Inventory', 14, 22);

  const columns = ['ID', 'Name', 'Description', 'SKU', 'Cost Price', 'Category', 'Stock', 'Units & Rates'];
  const rows = products.value.map(p => [
    p.id,
    p.name,
    p.description || '',
    p.sku,
    p.cost_price,
    p.category_name || '',
    p.quantity,
    p.units.map(u => `${u.unit_name} (${u.conversion_quantity} base) ${u.retail_price} UGX`).join('\n')
  ]);

  doc.autoTable({ head: [columns], body: rows, startY: 30 });
  doc.save('products_inventory.pdf');
};

// Category Modal
const openCategoryModal = (cat = null) => {
  editingCategory.value = cat;
  categoryForm.value = cat ? { ...cat } : { name: '', description: '' };
  showCategoryModal.value = true;
};

const saveCategory = async () => {
  if (!categoryForm.value.name.trim()) return notify('Category name required');
  try {
    if (editingCategory.value) {
      await api.put(`/inventory/categories/${categoryForm.value.id}`, categoryForm.value);
      notify('Category updated');
    } else {
      await api.post('/inventory/categories', categoryForm.value);
      notify('Category added');
    }
    showCategoryModal.value = false;
    fetchCategories();
  } catch {
    notify('Error saving category');
  }
};

const deleteCategory = async (id) => {
  if (!confirm('Delete category?')) return;
  try {
    await api.delete(`/inventory/categories/${id}`);
    notify('Category deleted');
    fetchCategories();
  } catch {
    notify('Failed to delete');
  }
};

// Utils
const formatPrice = (val) => {
  return new Intl.NumberFormat('en-UG', { style: 'currency', currency: 'UGX' }).format(val || 0);
};

const notify = (msg, duration = 3000) => {
  notification.value = msg;
  setTimeout(() => notification.value = '', duration);
};

onMounted(() => {
  fetchCategories();
  fetchProducts();
});
</script>

<style scoped>
.input {
  @apply w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition;
}
.btn-primary {
  @apply bg-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-blue-700 shadow-lg transition;
}
.btn-secondary {
  @apply bg-gray-500 text-white px-6 py-3 rounded-xl font-medium hover:bg-gray-600 transition;
}
.btn-gray {
  @apply bg-gray-300 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-400 transition;
}
.btn-sm {
  @apply px-3 py-1.5 text-xs rounded-lg text-white font-medium transition;
}
.th {
  @apply px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b;
}
.td {
  @apply px-4 py-3 text-sm border-b;
}
</style>