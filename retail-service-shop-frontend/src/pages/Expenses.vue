<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Expenses Management</h1>

    <!-- Add Expense Button -->
    <button
      @click="showModal = true"
      class="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105 mb-4"
    >
      + Add Expense
    </button>

    <!-- Grand Total -->
    <div class="mb-4 p-4 bg-gray-100 rounded shadow hover:shadow-lg transition transform hover:scale-[1.01]">
      <h2 class="text-lg font-bold">
        Grand Total Paid: <span class="text-green-600">{{ formatCurrency(grandTotal) }}</span>
      </h2>
    </div>

    <!-- Search + Date Filter + Export -->
    <div class="mb-6 flex flex-wrap items-end gap-3">
      <!-- Search -->
      <div class="flex-1 min-w-[220px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
        <input
          v-model="searchQuery"
          placeholder="Description, reference, item name..."
          class="border p-2 rounded w-full shadow-sm focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- From Date -->
      <div class="min-w-[180px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">From Date</label>
        <input
          v-model="dateRange.start"
          type="date"
          class="border p-2 rounded w-full shadow-sm focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- To Date -->
      <div class="min-w-[180px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">To Date</label>
        <input
          v-model="dateRange.end"
          type="date"
          class="border p-2 rounded w-full shadow-sm focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-2 flex-wrap">
        <button
          @click="applyFilters"
          class="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded shadow transition transform hover:scale-105"
        >
          Filter
        </button>

        <button
          @click="resetFilters"
          class="bg-gray-500 hover:bg-gray-600 text-white px-5 py-2 rounded shadow transition transform hover:scale-105"
        >
          Reset
        </button>

        <button
          @click="exportExcel"
          class="bg-yellow-500 hover:bg-yellow-600 text-white px-5 py-2 rounded shadow transition transform hover:scale-105"
        >
          Excel
        </button>

        <button
          @click="exportPDF"
          class="bg-red-500 hover:bg-red-600 text-white px-5 py-2 rounded shadow transition transform hover:scale-105"
        >
          PDF
        </button>

        <button
          @click="showItemModal = true"
          class="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded shadow transition transform hover:scale-105"
        >
          + New Item
        </button>
      </div>
    </div>

    <!-- Expenses Table -->
    <div class="overflow-x-auto border rounded-lg shadow-lg">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-3 border-b text-center"></th>
            <th class="p-3 border-b text-left">ID</th>
            <th class="p-3 border-b text-left">Description</th>
            <th class="p-3 border-b text-right">Total Amount</th>
            <th class="p-3 border-b text-left">Reference</th>
            <th class="p-3 border-b text-left">Expense Date</th>
            <th class="p-3 border-b text-left">Transaction No</th>
            <th class="p-3 border-b text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(expense, index) in expenses" :key="expense.id">
            <tr
              class="transition-all duration-300 hover:bg-gray-50 hover:shadow-sm cursor-pointer transform hover:scale-[1.01]"
            >
              <td class="p-3 text-center">
                <button @click="toggleExpand(expense.id)" class="text-blue-600 font-bold transition transform hover:scale-110">
                  {{ expandedRows.includes(expense.id) ? '−' : '+' }}
                </button>
              </td>
              <td class="p-3">{{ expense.id }}</td>
              <td class="p-3">{{ expense.description }}</td>
              <td class="p-3 text-right">{{ formatCurrency(expense.total_amount) }}</td>
              <td class="p-3">{{ expense.reference }}</td>
              <td class="p-3">{{ expense.expense_date }}</td>
              <td class="p-3">{{ expense.transaction_no }}</td>
              <td class="p-3 text-center flex flex-wrap gap-1 justify-center">
                <button @click="editExpense(expense)" class="bg-blue-400 hover:bg-blue-500 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">Edit</button>
                <button @click="deleteExpense(expense.id)" class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">Delete</button>
                <router-link :to="`/reports/expenses/${expense.id}`" class="text-indigo-600 underline hover:text-indigo-800 transition">
                  View
                </router-link>
              </td>
            </tr>

            <!-- Expanded row -->
            <tr v-show="expandedRows.includes(expense.id)">
              <td colspan="8" class="p-0">
                <div class="p-4 bg-gray-50 border-t shadow-inner">
                  <h3 class="font-semibold mb-2">Expense Items</h3>
                  <table class="w-full border text-sm">
                    <thead>
                      <tr>
                        <th class="p-2 border">Account</th>
                        <th class="p-2 border">Item Name</th>
                        <th class="p-2 border">Description</th>
                        <th class="p-2 border">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in expense.items" :key="`item-${item.id}`" class="hover:bg-gray-100 transition">
                        <td class="p-2 border">{{ getAccountName(item.account_id) }}</td>
                        <td class="p-2 border">{{ item.item_name }}</td>
                        <td class="p-2 border">{{ item.description }}</td>
                        <td class="p-2 border text-right">{{ formatCurrency(item.amount) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </td>
            </tr>
          </template>

          <!-- No data message -->
          <tr v-if="expenses.length === 0">
            <td colspan="8" class="p-8 text-center text-gray-500">
              No expenses found for the selected period / search.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Controls -->
    <div v-if="pagination.total > 0" class="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm">
      <div class="text-gray-700">
        Showing
        <span class="font-medium">{{ (pagination.current_page - 1) * pagination.per_page + 1 }}</span>
        to
        <span class="font-medium">{{ Math.min(pagination.current_page * pagination.per_page, pagination.total) }}</span>
        of
        <span class="font-medium">{{ pagination.total }}</span>
        results
      </div>

      <div class="flex items-center gap-3">
        <button
          @click="changePage(pagination.current_page - 1)"
          :disabled="!pagination.has_prev"
          class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Previous
        </button>

        <span class="px-4 py-2 font-medium text-gray-800">
          Page {{ pagination.current_page }} of {{ pagination.pages }}
        </span>

        <button
          @click="changePage(pagination.current_page + 1)"
          :disabled="!pagination.has_next"
          class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Next
        </button>

        <select
          v-model="perPage"
          @change="applyFilters"
          class="border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          <option :value="10">10 per page</option>
          <option :value="20">20 per page</option>
          <option :value="50">50 per page</option>
          <option :value="100">100 per page</option>
        </select>
      </div>
    </div>

    <!-- Add/Edit Expense Modal -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 animate-fadeInModal">
      <div class="bg-white rounded-lg p-6 w-full max-w-[806px] relative shadow-xl transform transition-all scale-95 animate-scaleUp">
        <h2 class="text-xl font-bold mb-4">{{ editingExpense ? 'Edit Expense' : 'Add Expense' }}</h2>
        <button @click="closeModal" class="absolute top-2 right-2 text-gray-600 hover:text-gray-800 transition transform hover:scale-110">✖</button>

        <div class="grid grid-cols-2 gap-4 mb-4">
          <input v-model="expenseForm.description" placeholder="Expense Description" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input v-model="expenseForm.reference" placeholder="Reference" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input 
            list="paymentAccounts" 
            v-model="expenseForm.payment_account_name" 
            placeholder="Payment Account (Cash/Bank)" 
            class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" 
            @focus="fetchCashBankAccounts('')"
          />
          <datalist id="paymentAccounts">
            <option v-for="acc in cashBankAccounts" :key="acc.id" :value="acc.name"></option>
          </datalist>
          <input v-model="expenseForm.expense_date" type="date" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
        </div>

        <h3 class="font-bold mb-2">Expense Items</h3>
        <div v-for="(item, index) in expenseForm.items" :key="`item-${index}`" class="grid grid-cols-5 gap-2 mb-2">
          <input 
            list="expenseAccounts" 
            v-model="item.account_name" 
            placeholder="Select Expense Account" 
            class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" 
            @focus="fetchExpenseAccounts('')"
          />
          <datalist id="expenseAccounts">
            <option v-for="acc in expenseAccounts" :key="acc.id" :value="acc.name"></option>
          </datalist>
          <input v-model="item.item_name" placeholder="Item Name" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input v-model="item.description" placeholder="Item Description" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input v-model.number="item.amount" type="number" placeholder="Amount" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <button type="button" @click="removeItem(index)" class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">✖</button>
        </div>

        <button type="button" @click="addItem" class="bg-gray-300 hover:bg-gray-400 px-4 py-2 rounded shadow transition transform hover:scale-105 mb-4">+ Add Item</button>

        <div class="mb-4">
          <label class="block text-sm font-bold mb-1">Amount Paid</label>
          <input type="number" :value="amountPaid.toFixed(2)" class="border p-2 rounded w-full bg-gray-100" disabled />
        </div>

        <div class="flex justify-end">
          <button @click="submitExpense" class="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded shadow transition transform hover:scale-105">
            {{ editingExpense ? 'Update Expense' : 'Create Expense' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add Expense Item Modal -->
    <div v-if="showItemModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 animate-fadeInModal">
      <div class="bg-white rounded-lg p-6 w-full max-w-md relative shadow-xl transform transition-all scale-95 animate-scaleUp">
        <h2 class="text-xl font-bold mb-4">Add Expense Item</h2>
        <button @click="closeItemModal" class="absolute top-2 right-2 text-gray-600 hover:text-gray-800 transition transform hover:scale-110">✖</button>

        <div class="grid gap-4 mb-4">
          <input v-model="expenseItemForm.name" placeholder="Expense Item Name" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />

          <select v-model="expenseItemForm.account_subtype" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition">
            <option value="" disabled>Select Expense Type</option>
            <option v-for="acc in expenseSubtypes" :key="acc" :value="acc">{{ acc }}</option>
          </select>
        </div>

        <div class="flex justify-end">
          <button @click="submitExpenseItem" class="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded shadow transition transform hover:scale-105">
            Save Item
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../api";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import "jspdf-autotable";

export default {
  data() {
    const today = new Date().toISOString().split("T")[0];
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    const defaultStart = oneMonthAgo.toISOString().split("T")[0];

    return {
      expenses: [],
      searchQuery: "",
      dateRange: {
        start: defaultStart,
        end: today,
      },
      pagination: {
        total: 0,
        pages: 0,
        current_page: 1,
        per_page: 10,
        has_next: false,
        has_prev: false,
      },
      perPage: 10,
      showModal: false,
      editingExpense: false,
      expandedRows: [],
      expenseForm: {
        id: null,
        description: "",
        payment_account_name: "",
        payment_account_id: null,
        expense_date: today,
        reference: "",
        items: [{ account_name: "", account_id: null, item_name: "", description: "", amount: 0 }],
      },
      cashBankAccounts: [],
      expenseAccounts: [],
      showItemModal: false,
      expenseItemForm: {
        name: "",
        account_subtype: "",
      },
      expenseSubtypes: [],
    };
  },

  computed: {
    grandTotal() {
      return this.expenses.reduce((sum, expense) => sum + Number(expense.total_amount || 0), 0);
    },
    amountPaid() {
      return this.expenseForm.items.reduce((total, item) => total + Number(item.amount || 0), 0);
    },
  },

  methods: {
    formatCurrency(value) {
      if (!value && value !== 0) return "UGX 0";
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'UGX',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    },

    getAccountName(accountId) {
      const acc = this.expenseAccounts.find(a => a.id === accountId);
      return acc ? acc.name : "Unknown Account";
    },

    async fetchCashBankAccounts(search = "") {
      try {
        const res = await api.get("/accounts/cash-bank", { params: { search } });
        this.cashBankAccounts = res.data;
      } catch (err) {
        console.error("Error fetching cash/bank accounts:", err);
      }
    },

    async fetchExpenseAccounts(search = "") {
      try {
        const res = await api.get("/accounts/expense-account", { params: { search } });
        this.expenseAccounts = res.data;
      } catch (err) {
        console.error("Error fetching expense accounts:", err);
      }
    },

    async fetchExpenseSubtypes() {
      try {
        const res = await api.get("/accounts/");
        this.expenseSubtypes = [...new Set(res.data.filter(a => a.account_type === "EXPENSE").map(a => a.account_subtype))];
      } catch (err) {
        console.error("Error fetching expense subtypes:", err);
      }
    },

    addItem() {
      this.expenseForm.items.push({ account_name: "", account_id: null, item_name: "", description: "", amount: 0 });
    },

    removeItem(index) {
      this.expenseForm.items.splice(index, 1);
    },

    closeItemModal() {
      this.expenseItemForm = { name: "", account_subtype: "" };
      this.showItemModal = false;
    },

    validateExpense() {
      if (!this.expenseForm.description.trim()) {
        alert("Expense description is required.");
        return false;
      }
      if (!this.expenseForm.payment_account_id) {
        alert("Please select a valid payment account.");
        return false;
      }
      if (!this.expenseForm.expense_date) {
        alert("Expense date is required.");
        return false;
      }
      if (this.expenseForm.items.length === 0) {
        alert("At least one expense item is required.");
        return false;
      }
      for (const [i, item] of this.expenseForm.items.entries()) {
        if (!item.account_id) {
          alert(`Item ${i + 1}: Valid expense account is required.`);
          return false;
        }
        if (!item.item_name.trim()) {
          alert(`Item ${i + 1}: Item name is required.`);
          return false;
        }
        if (!item.amount || item.amount <= 0) {
          alert(`Item ${i + 1}: Amount must be greater than 0.`);
          return false;
        }
      }
      return true;
    },

    async submitExpense() {
      const paymentAcc = this.cashBankAccounts.find(a => a.name === this.expenseForm.payment_account_name);
      if (!paymentAcc) {
        alert("Please select a valid Cash/Bank account!");
        return;
      }
      this.expenseForm.payment_account_id = paymentAcc.id;

      for (const item of this.expenseForm.items) {
        const acc = this.expenseAccounts.find(a => a.name === item.account_name);
        if (!acc) {
          alert(`Invalid expense account for item "${item.item_name}"`);
          return;
        }
        item.account_id = acc.id;
      }

      if (!this.validateExpense()) return;

      try {
        if (this.editingExpense) {
          await api.put(`/expenses/${this.expenseForm.id}`, this.expenseForm);
          alert("✅ Expense updated successfully!");
        } else {
          await api.post("/expenses/", this.expenseForm);
          alert("✅ Expense created successfully!");
        }
        this.closeModal();
        this.fetchExpenses();
      } catch (err) {
        console.error("❌ Error submitting expense:", err);
        alert("Failed to submit expense. " + (err.response?.data?.error || err.message));
      }
    },

    async submitExpenseItem() {
      if (!this.expenseItemForm.name.trim() || !this.expenseItemForm.account_subtype) {
        alert("Expense Item Name and Type are required!");
        return;
      }

      try {
        const payload = {
          name: this.expenseItemForm.name.trim(),
          account_subtype: this.expenseItemForm.account_subtype
        };

        await api.post("/accounts/expense-items", payload);
        alert(`✅ Expense Item "${this.expenseItemForm.name}" created successfully!`);

        await this.fetchExpenseAccounts();
        this.closeItemModal();
      } catch (err) {
        console.error("❌ Error creating expense item:", err);
        alert("Failed to create expense item. " + (err.response?.data?.error || err.message));
      }
    },

    editExpense(expense) {
      this.expenseForm = {
        id: expense.id,
        description: expense.description,
        payment_account_name: this.cashBankAccounts.find(a => a.id === expense.payment_account_id)?.name || "",
        payment_account_id: expense.payment_account_id,
        expense_date: expense.expense_date.split("T")[0],
        reference: expense.reference,
        items: expense.items.map(i => ({
          account_name: this.expenseAccounts.find(a => a.id === i.account_id)?.name || "",
          account_id: i.account_id,
          item_name: i.item_name,
          description: i.description,
          amount: i.amount
        })),
      };
      this.editingExpense = true;
      this.showModal = true;
    },

    closeModal() {
      this.resetForm();
      this.showModal = false;
    },

    resetForm() {
      const today = new Date().toISOString().split("T")[0];
      this.expenseForm = {
        id: null,
        description: "",
        payment_account_name: "",
        payment_account_id: null,
        expense_date: today,
        reference: "",
        items: [{ account_name: "", account_id: null, item_name: "", description: "", amount: 0 }],
      };
      this.editingExpense = false;
    },

    async fetchExpenses() {
      try {
        const params = {
          page: this.pagination.current_page,
          per_page: this.perPage,
          search: this.searchQuery || undefined,
          start_date: this.dateRange.start || undefined,
          end_date: this.dateRange.end || undefined,
        };

        const cleanParams = Object.fromEntries(
          Object.entries(params).filter(([_, value]) => value !== undefined)
        );

        const res = await api.get("/expenses/", { params: cleanParams });

        this.expenses = res.data.data || [];
        this.pagination = {
          total: res.data.pagination.total || 0,
          pages: res.data.pagination.pages || 1,
          current_page: res.data.pagination.current_page || 1,
          per_page: res.data.pagination.per_page || this.perPage,
          has_next: res.data.pagination.has_next || false,
          has_prev: res.data.pagination.has_prev || false,
        };
      } catch (err) {
        console.error("❌ Error fetching expenses:", err);
        alert("Failed to load expenses. Please try again.");
      }
    },

    changePage(page) {
      if (page < 1 || page > this.pagination.pages) return;
      this.pagination.current_page = page;
      this.fetchExpenses();
    },

    applyFilters() {
      if (this.dateRange.start && this.dateRange.end && this.dateRange.start > this.dateRange.end) {
        alert("Start date cannot be later than end date.");
        return;
      }
      this.pagination.current_page = 1; // Reset to first page on filter
      this.fetchExpenses();
    },

    resetFilters() {
      this.searchQuery = "";
      const today = new Date().toISOString().split("T")[0];
      const oneMonthAgo = new Date();
      oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

      this.dateRange = {
        start: oneMonthAgo.toISOString().split("T")[0],
        end: today,
      };
      this.pagination.current_page = 1;
      this.fetchExpenses();
    },

    async deleteExpense(id) {
      if (!confirm("Are you sure you want to delete this expense?")) return;

      try {
        await api.delete(`/expenses/${id}`);
        alert("🗑️ Expense deleted successfully!");
        this.fetchExpenses();
      } catch (err) {
        console.error("❌ Error deleting expense:", err);
        alert("Failed to delete expense.");
      }
    },

    toggleExpand(id) {
      if (this.expandedRows.includes(id)) {
        this.expandedRows = this.expandedRows.filter(rowId => rowId !== id);
      } else {
        this.expandedRows.push(id);
      }
    },

    exportExcel() {
      try {
        const ws = XLSX.utils.json_to_sheet(this.expenses);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Expenses");
        XLSX.writeFile(wb, "expenses.xlsx");
      } catch (err) {
        console.error("❌ Error exporting Excel:", err);
        alert("Failed to export Excel.");
      }
    },

    exportPDF() {
      try {
        const doc = new jsPDF();
        doc.autoTable({
          head: [["ID", "Description", "Total Amount", "Reference", "Expense Date", "Transaction No"]],
          body: this.expenses.map(e => [
            e.id,
            e.description,
            e.total_amount,
            e.reference,
            e.expense_date,
            e.transaction_no
          ])
        });
        doc.save("expenses.pdf");
      } catch (err) {
        console.error("❌ Error exporting PDF:", err);
        alert("Failed to export PDF.");
      }
    },
  },

  watch: {
    perPage() {
      this.pagination.current_page = 1;
      this.fetchExpenses();
    },
  },

  mounted() {
    this.fetchExpenses();
    this.fetchCashBankAccounts();
    this.fetchExpenseAccounts();
    this.fetchExpenseSubtypes();
  }
};
</script>

<style scoped>
@keyframes fadeInModal {
  0% { opacity: 0; }
  100% { opacity: 1; }
}
.animate-fadeInModal { animation: fadeInModal 0.3s ease-in-out forwards; }

@keyframes scaleUp {
  0% { transform: scale(0.95); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.animate-scaleUp { animation: scaleUp 0.3s ease-out forwards; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn { animation: fadeIn 0.5s ease-in-out forwards; }
</style>