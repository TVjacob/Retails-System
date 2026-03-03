<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-semibold mb-6 text-gray-800">📦 Stock Adjustments</h1>

    <!-- Create Adjustment Form -->
    <form @submit.prevent="submitAdjustment" class="bg-white p-6 rounded-2xl shadow-md space-y-6 mb-8">
      <h2 class="text-xl font-semibold text-gray-800">New Stock Adjustment</h2>

      <div class="grid md:grid-cols-3 gap-6">
        <!-- Product Search -->
        <div class="relative">
          <label class="label">Product *</label>
          <input
            type="text"
            v-model="searchProduct"
            class="input"
            placeholder="Search product..."
            @focus="showDropdown = true"
            @input="showDropdown = true"
            required
            :disabled="loading"
          />

          <!-- Product Dropdown -->
          <ul
            v-if="showDropdown"
            class="absolute z-20 w-full bg-white border rounded-lg max-h-60 overflow-auto shadow-lg mt-1"
          >
            <li
              v-for="p in filteredProducts"
              :key="p.id"
              @click="selectProduct(p)"
              class="px-4 py-3 hover:bg-indigo-50 cursor-pointer transition"
            >
              {{ p.name }} (Stock: {{ p.quantity.toFixed(2) }} base)
            </li>
            <li v-if="filteredProducts.length === 0" class="px-4 py-3 text-gray-500">
              No products found
            </li>
          </ul>
        </div>

        <!-- Unit Selection -->
        <div>
          <label class="label">Unit *</label>
          <select
            v-model="form.unit_id"
            class="input"
            required
            :disabled="!selectedProduct || loading"
          >
            <option value="">Select unit</option>
            <option v-for="unit in units" :key="unit.id" :value="unit.id">
              {{ unit.unit_name }} (1 = {{ unit.conversion_quantity }} base)
            </option>
          </select>
        </div>

        <!-- Adjustment Type -->
        <div>
          <label class="label">Adjustment Type *</label>
          <select v-model="form.adjustment_type" class="input" required :disabled="loading">
            <option value="">Select Type</option>
            <option value="INCREASE">Increase (+)</option>
            <option value="DECREASE">Decrease (-)</option>
          </select>
        </div>
      </div>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Quantity Change -->
        <div>
          <label class="label">Quantity Change (in selected unit) *</label>
          <input
            type="number"
            min="0.01"
            step="0.01"
            v-model.number="form.quantity_change"
            class="input"
            required
            :disabled="loading || !form.unit_id"
          />
        </div>

        <!-- Reason -->
        <div>
          <label class="label">Reason / Note</label>
          <input
            v-model="form.reason"
            class="input"
            placeholder="e.g. Damaged, Received extra, Counting error..."
            :disabled="loading"
          />
        </div>
      </div>

      <!-- Current Stock Info (after unit selected) -->
      <div v-if="form.unit_id && selectedProduct" class="bg-indigo-50 p-4 rounded-xl text-sm">
        <p class="font-medium">
          Current stock in <strong>{{ selectedUnitName }}</strong>:
          <span class="text-indigo-700 font-bold">{{ currentStockInUnit.toFixed(3) }}</span>
        </p>
        <p class="text-gray-600 mt-1">
          Expected new stock: 
          <strong>{{ (currentStockInUnit + calculatedChange).toFixed(3) }}</strong>
        </p>
      </div>

      <div class="flex justify-end">
        <button
          type="submit"
          class="btn-primary px-8 py-3"
          :disabled="loading || !isFormValid"
        >
          {{ loading ? 'Processing...' : 'Submit Adjustment' }}
        </button>
      </div>
    </form>

    <!-- Adjustment History -->
    <div class="bg-white p-6 rounded-2xl shadow-md">
      <h2 class="text-xl font-semibold text-gray-800 mb-4">Adjustment History</h2>

      <div class="overflow-x-auto">
        <table class="min-w-full border-collapse text-sm">
          <thead class="bg-gray-100">
            <tr>
              <th class="th">Date</th>
              <th class="th">Product</th>
              <th class="th">Unit</th>
              <th class="th">Adjusted quantity</th>

              <th class="th text-center">Qty Change</th>
              <th class="th text-center">Prev Stock (unit)</th>
              <th class="th text-center">New Stock (unit)</th>
              <th class="th">Reason</th>
              <th class="th text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="adj in adjustments" :key="adj.id" class="hover:bg-indigo-50 transition">
              <td class="td">{{ formatDate(adj.adjusted_at) }}</td>
              <td class="td">{{ adj.product_name }}</td>
              <td class="td">{{ adj.unit_name || 'Base' }}</td>
              <td class="td">{{ adj.quantity || '0' }}</td>

              <td class="td text-center font-medium" :class="adj.adjustment_type === 'INCREASE' ? 'text-green-600' : 'text-red-600'">
                {{ adj.adjustment_type === 'INCREASE' ? '+' : '-' }}{{ adj.quantity_change }}
              </td>
              <td class="td text-center">{{ adj.previous_quantity?.toFixed(3) || '—' }}</td>
              <td class="td text-center font-semibold">{{ adj.new_quantity?.toFixed(3) || '—' }}</td>
              <td class="td">{{ adj.reason || '—' }}</td>
              <td class="td text-center">
                <button
                  @click="deleteAdjustment(adj.id)"
                  class="btn-sm bg-red-500 hover:bg-red-600"
                  :disabled="loading"
                >
                  Delete
                  
                </button>
              </td>
            </tr>
            <tr v-if="adjustments.length === 0">
              <td colspan="8" class="text-center py-8 text-gray-500">
                No adjustments recorded yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Notification -->
    <transition name="fade">
      <div
        v-if="notification"
        class="fixed bottom-6 right-6 bg-gray-900 text-white px-6 py-4 rounded-xl shadow-2xl text-sm z-50"
      >
        {{ notification }}
      </div>
    </transition>
  </div>
</template>

<script>
import api from "../api";

export default {
  data() {
    return {
      products: [],
      adjustments: [],
      notification: "",
      searchProduct: "",
      showDropdown: false,
      loading: false,

      selectedProduct: null,
      units: [],

      form: {
        product_id: "",
        unit_id: null,
        adjustment_type: "",
        quantity_change: 1,
        reason: "",
      },
    };
  },

  computed: {
    filteredProducts() {
      if (!this.searchProduct) return this.products;
      return this.products.filter((p) =>
        p.name.toLowerCase().includes(this.searchProduct.toLowerCase())
      );
    },

    currentStockInUnit() {
      if (!this.selectedProduct || !this.form.unit_id) return 0;
      const unit = this.units.find(u => u.id === this.form.unit_id);
      if (!unit || unit.conversion_quantity === 0) return this.selectedProduct.quantity;
      return this.selectedProduct.quantity / unit.conversion_quantity;
    },

    calculatedChange() {
      if (this.form.adjustment_type === "INCREASE") return this.form.quantity_change || 0;
      if (this.form.adjustment_type === "DECREASE") return -(this.form.quantity_change || 0);
      return 0;
    },

    selectedUnitName() {
      if (!this.form.unit_id) return "Base Unit";
      const unit = this.units.find(u => u.id === this.form.unit_id);
      return unit ? unit.unit_name : "Base Unit";
    },

    isFormValid() {
      return (
        this.form.product_id &&
        this.form.unit_id &&
        this.form.adjustment_type &&
        this.form.quantity_change > 0
      );
    },
  },

  methods: {
    async fetchProducts() {
      try {
        const res = await api.get("/inventory/products");
        this.products = res.data;
      } catch (err) {
        console.error("Failed to load products", err);
      }
    },

    async fetchAdjustments() {
      try {
        const res = await api.get("/stock-adjustments/");
        this.adjustments = res.data;
      } catch (err) {
        console.error("Failed to load adjustments", err);
      }
    },

    selectProduct(product) {
      this.selectedProduct = product;
      this.form.product_id = product.id;
      this.searchProduct = product.name;
      this.showDropdown = false;

      // Load units for this product
      this.units = product.units || [];
      this.form.unit_id = null; // reset unit
    },

    formatDate(dateStr) {
      if (!dateStr) return "—";
      return new Date(dateStr).toLocaleString("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
      });
    },

    showNotification(msg, type = "success") {
      this.notification = msg;
      setTimeout(() => (this.notification = ""), 4000);
    },

    async submitAdjustment() {
      if (!this.isFormValid) return;

      this.loading = true;

      try {
        const payload = { ...this.form };

        await api.post("/stock-adjustments/", payload);

        this.showNotification("Stock adjustment applied successfully!");
        this.resetForm();
        await this.fetchAdjustments();
        await this.fetchProducts(); // refresh product stock
      } catch (err) {
        this.showNotification(
          err.response?.data?.error || "Failed to adjust stock",
          "error"
        );
      } finally {
        this.loading = false;
      }
    },

    resetForm() {
      this.form = {
        product_id: "",
        unit_id: null,
        adjustment_type: "",
        quantity_change: 1,
        reason: "",
      };
      this.searchProduct = "";
      this.selectedProduct = null;
      this.units = [];
    },

    async deleteAdjustment(id) {
      if (!confirm("Are you sure you want to delete this adjustment?")) return;

      this.loading = true;
      try {
        await api.delete(`/stock-adjustments/${id}`);
        this.showNotification("Adjustment deleted successfully");
        await this.fetchAdjustments();
        await this.fetchProducts();
      } catch (err) {
        this.showNotification("Failed to delete adjustment", "error");
      } finally {
        this.loading = false;
      }
    },
  },

  mounted() {
    this.fetchProducts();
    this.fetchAdjustments();

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!this.$el.contains(e.target)) {
        this.showDropdown = false;
      }
    });
  },
};
</script>

<style scoped>
.label {
  @apply text-gray-700 font-medium text-sm mb-1.5 block;
}
.input {
  @apply border border-gray-300 rounded-lg px-4 py-2.5 w-full focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition;
}
.btn-primary {
  @apply bg-indigo-600 text-white px-6 py-3 rounded-xl hover:bg-indigo-700 transition shadow font-medium;
}
.th {
  @apply border p-3 bg-gray-100 font-semibold text-gray-700 text-left;
}
.td {
  @apply border p-3 text-gray-700;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>