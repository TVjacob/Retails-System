<template>
  <div class="p-6 max-w-7xl mx-auto space-y-8 bg-gray-50 dark:bg-gray-950 min-h-screen">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 tracking-tight">
        Expenses Management
      </h1>
      <button
        @click="showModal = true"
        class="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg shadow-md transition transform hover:scale-105 flex items-center gap-2 font-medium"
      >
        <span>+</span> Add Expense
      </button>
    </div>

    <!-- Grand Total Card -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-6">
      <div class="flex justify-between items-center">
        <h2 class="text-lg font-semibold text-black">
          Total Expenses Recorded
        </h2>
        <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
          {{ formatCurrency(grandTotal) }}
        </p>
      </div>
    </div>

    <!-- Filters & Actions -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700 p-6">
      <div class="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-5">
        <!-- Search -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">Search</label>
          <input
            v-model="searchQuery"
            placeholder="Description, item, reference..."
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
        </div>

        <!-- From Date -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">From Date</label>
          <input
            v-model="dateRange.start"
            type="date"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
        </div>

        <!-- To Date -->
        <div>
          <label class="block text-sm font-medium text-black mb-1.5">To Date</label>
          <input
            v-model="dateRange.end"
            type="date"
            class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
        </div>

        <!-- Buttons -->
        <div class="flex items-end gap-3 flex-wrap">
          <button
            @click="applyFilters"
            class="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg shadow transition transform hover:scale-105 font-medium"
          >
            Apply Filter
          </button>
          <button
            @click="resetFilters"
            class="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2.5 rounded-lg shadow transition transform hover:scale-105 font-medium"
          >
            Reset
          </button>
        </div>

        <div class="flex items-end gap-3 flex-wrap">
          <button
            @click="exportExcel"
            class="bg-amber-600 hover:bg-amber-700 text-white px-5 py-2.5 rounded-lg shadow transition transform hover:scale-105 font-medium"
          >
            Export Excel
          </button>
          <button
            @click="exportPDF"
            class="bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-lg shadow transition transform hover:scale-105 font-medium"
          >
            Export PDF
          </button>
        </div>
      </div>
    </div>

    <!-- Expenses Table -->
    <div class="overflow-x-auto bg-white dark:bg-gray-800 rounded-2xl shadow border border-gray-200 dark:border-gray-700">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-900/60 sticky top-0 z-10">
          <tr>
            <th class="w-12 p-4 text-center"></th>
            <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">ID</th>
            <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Description</th>
            <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider min-w-[300px]">Narration</th>
            <th class="p-4 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Total</th>
            <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Reference</th>
            <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Date</th>
            <th class="p-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Trans. #</th>
            <th class="p-4 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <template v-for="expense in filteredExpenses" :key="expense.id">
            <!-- Main Row -->
            <tr
              class="hover:bg-indigo-50/40 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
              @click="toggleExpand(expense.id)"
            >
              <td class="p-4 text-center">
                <span class="text-indigo-600 dark:text-indigo-400 font-bold text-lg">
                  {{ expandedRows.includes(expense.id) ? '−' : '+' }}
                </span>
              </td>
              <td class="p-4 text-black font-medium">{{ expense.id }}</td>
              <td class="p-4 text-black font-medium">{{ expense.description }}</td>

              <td
                class="p-4 text-black text-sm max-w-md group relative line-clamp-3 hover:line-clamp-none transition-all duration-200"
                :title="getFullNarration(expense.items)"
              >
                <div v-if="expense.items?.length > 0">
                  <div v-if="expense.items.length === 1" class="line-clamp-3">
                    {{ expense.items[0].description || '—' }}
                  </div>
                  <div v-else class="italic text-black line-clamp-3">
                    {{ expense.items[0]?.description || 'Multiple narrations' }}
                    <span class="text-xs text-black">
                      (+{{ expense.items.length - 1 }} more)
                    </span>
                  </div>
                </div>
                <span v-else class="text-black italic">No narration provided</span>

                <div v-if="expense.items?.length > 0 && expense.items.some(i => i.description?.length > 80)"
                     class="absolute hidden group-hover:block z-20 bg-gray-900 text-white text-sm rounded p-3 shadow-xl w-96 -mt-2 left-0 top-full border border-gray-700">
                  <div class="space-y-2">
                    <div v-for="(item, idx) in expense.items" :key="idx" class="border-b border-gray-700 pb-2 last:border-0">
                      <p class="font-medium">{{ item.item_name }}</p>
                      <p class="text-gray-300">{{ item.description || '—' }}</p>
                    </div>
                  </div>
                </div>
              </td>

              <td class="p-4 text-right font-semibold text-emerald-700 dark:text-emerald-400">
                {{ formatCurrency(expense.total_amount) }}
              </td>
              <td class="p-4 text-black">{{ expense.reference || '—' }}</td>
              <td class="p-4 text-black">{{ expense.expense_date }}</td>
              <td class="p-4 text-black">{{ expense.transaction_no || '—' }}</td>
              <td class="p-4 text-center">
                <div class="flex justify-center gap-2 flex-wrap">
                  <button
                    @click.stop="editExpense(expense)"
                    class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1.5 rounded shadow-sm transition"
                  >
                    Edit
                  </button>
                  <button
                    @click.stop="deleteExpense(expense.id)"
                    class="bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1.5 rounded shadow-sm transition"
                  >
                    Delete
                  </button>
                  <router-link
                    :to="`/reports/expenses/${expense.id}`"
                    class="text-indigo-500 dark:text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-300 text-xs font-medium px-3 py-1.5 transition"
                  >
                    View
                  </router-link>
                </div>
              </td>
            </tr>

            <!-- Expanded Row -->
            <tr v-if="expandedRows.includes(expense.id)">
              <td colspan="9" class="p-0">
                <div class="p-6 bg-gray-50 dark:bg-gray-900/40 border-t border-gray-200 dark:border-gray-700">
                  <h4 class="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <span>Expense Breakdown</span>
                    <span class="text-sm font-normal text-gray-500 dark:text-gray-400">
                      ({{ expense.items.length }} item{{ expense.items.length !== 1 ? 's' : '' }})
                    </span>
                  </h4>

                  <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                    <table class="min-w-full text-sm">
                      <thead class="bg-gray-100 dark:bg-gray-800/60">
                        <tr>
                          <th class="p-3 text-left font-medium text-gray-700 dark:text-gray-300">Account</th>
                          <th class="p-3 text-left font-medium text-gray-700 dark:text-gray-300">Item Name</th>
                          <th class="p-3 text-left font-medium text-gray-700 dark:text-gray-300">Narration</th>
                          <th class="p-3 text-right font-medium text-gray-700 dark:text-gray-300">Amount</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                        <tr v-for="item in expense.items" :key="item.id" class="hover:bg-white dark:hover:bg-gray-800/40 transition">
                          <td class="p-3 text-gray-900 dark:text-gray-200">{{ getAccountName(item.account_id) }}</td>
                          <td class="p-3 text-gray-900 dark:text-gray-200">{{ item.item_name }}</td>
                          <td class="p-3 text-gray-800 dark:text-gray-300">{{ item.description || '—' }}</td>
                          <td class="p-3 text-right font-medium text-emerald-700 dark:text-emerald-400">
                            {{ formatCurrency(item.amount) }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </td>
            </tr>
          </template>

          <tr v-if="filteredExpenses.length === 0">
            <td colspan="9" class="p-16 text-center text-gray-500 dark:text-gray-400 text-lg">
              No expenses found in the selected period.<br />
              <span class="text-sm mt-2 block">Try adjusting your filters or add a new expense.</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="pagination.total > 0" class="mt-8 flex flex-col sm:flex-row justify-between items-center gap-6 text-sm text-gray-700 dark:text-gray-300">
      <div>
        Showing
        <span class="font-medium">{{ (pagination.current_page - 1) * pagination.per_page + 1 }}</span>
        to
        <span class="font-medium">{{ Math.min(pagination.current_page * pagination.per_page, pagination.total) }}</span>
        of
        <span class="font-medium">{{ pagination.total }}</span> expenses
      </div>

      <div class="flex items-center gap-4">
        <button
          @click="changePage(pagination.current_page - 1)"
          :disabled="!pagination.has_prev"
          class="px-5 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition font-medium"
        >
          Previous
        </button>

        <span class="font-medium">
          Page {{ pagination.current_page }} / {{ pagination.pages }}
        </span>

        <button
          @click="changePage(pagination.current_page + 1)"
          :disabled="!pagination.has_next"
          class="px-5 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition font-medium"
        >
          Next
        </button>

        <select
          v-model="perPage"
          @change="applyFilters"
          class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        >
          <option :value="10">10 per page</option>
          <option :value="20">20 per page</option>
          <option :value="50">50 per page</option>
          <option :value="100">100 per page</option>
        </select>
      </div>
    </div>

    <!-- Add/Edit Modal (unchanged – keeping your original structure) -->
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

    <!-- Add Expense Item Modal (if you still use it) -->
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
  name: 'ExpenseManagement',
  data() {
    const today = new Date().toISOString().split("T")[0];
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    const defaultStart = oneMonthAgo.toISOString().split("T")[0];

    return {
      filteredExpenses: [],
      grandTotal: 0,
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
    amountPaid() {
      return this.expenseForm.items.reduce((total, item) => total + Number(item.amount || 0), 0);
    },
  },

  methods: {
    formatCurrency(value) {
      if (value == null) return "UGX 0";
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "UGX",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    },

    getFullNarration(items) {
      if (!items?.length) return "";
      return items.map(i => i.description || "—").join("\n\n");
    },

    getAccountName(accountId) {
      const acc = this.expenseAccounts.find(a => a.id === accountId);
      return acc ? acc.name : "Unknown";
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
      if (!this.expenseForm.description.trim()) return alert("Expense description is required."), false;
      if (!this.expenseForm.payment_account_id) return alert("Please select a valid payment account."), false;
      if (!this.expenseForm.expense_date) return alert("Expense date is required."), false;
      if (this.expenseForm.items.length === 0) return alert("At least one expense item is required."), false;

      for (const [i, item] of this.expenseForm.items.entries()) {
        if (!item.account_id) return alert(`Item ${i + 1}: Valid expense account is required.`), false;
        if (!item.item_name.trim()) return alert(`Item ${i + 1}: Item name is required.`), false;
        if (!item.amount || item.amount <= 0) return alert(`Item ${i + 1}: Amount must be greater than 0.`), false;
      }
      return true;
    },

    async submitExpense() {
      const paymentAcc = this.cashBankAccounts.find(a => a.name === this.expenseForm.payment_account_name);
      if (!paymentAcc) return alert("Please select a valid Cash/Bank account!"), false;
      this.expenseForm.payment_account_id = paymentAcc.id;

      for (const item of this.expenseForm.items) {
        const acc = this.expenseAccounts.find(a => a.name === item.account_name);
        if (!acc) return alert(`Invalid expense account for item "${item.item_name}"`), false;
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
        console.error("Error submitting expense:", err);
        alert("Failed to submit expense. " + (err.response?.data?.error || err.message));
      }
    },

    async submitExpenseItem() {
      if (!this.expenseItemForm.name.trim() || !this.expenseItemForm.account_subtype) {
        return alert("Expense Item Name and Type are required!");
      }

      try {
        await api.post("/accounts/expense-items", {
          name: this.expenseItemForm.name.trim(),
          account_subtype: this.expenseItemForm.account_subtype
        });
        alert(`✅ Expense Item "${this.expenseItemForm.name}" created!`);
        await this.fetchExpenseAccounts();
        this.closeItemModal();
      } catch (err) {
        console.error("Error creating expense item:", err);
        alert("Failed to create expense item.");
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
          Object.entries(params).filter(([, v]) => v !== undefined)
        );

        const res = await api.get("/expenses/", { params: cleanParams });

        this.filteredExpenses = res.data.data || [];
        this.grandTotal = res.data.grand_total?.total_expenses || 0;

        const p = res.data.pagination || {};
        this.pagination = {
          total: p.total_records || 0,
          pages: p.total_pages || 1,
          current_page: p.current_page || 1,
          per_page: p.per_page || this.perPage,
          has_next: p.has_next || false,
          has_prev: p.has_prev || false,
        };
      } catch (err) {
        console.error("Error fetching expenses:", err);
        alert("Failed to load expenses.");
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
      this.pagination.current_page = 1;
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
        console.error("Error deleting expense:", err);
        alert("Failed to delete expense.");
      }
    },

    toggleExpand(id) {
      if (this.expandedRows.includes(id)) {
        this.expandedRows = this.expandedRows.filter(r => r !== id);
      } else {
        this.expandedRows.push(id);
      }
    },

    exportExcel() {
      try {
        const rows = [];

        this.filteredExpenses.forEach(exp => {
          exp.items.forEach(item => {
            rows.push({
              "Exp ID": exp.id,
              "Date": exp.expense_date,
              "Description": exp.description,
              "Reference": exp.reference || "—",
              "Trans #": exp.transaction_no || "—",
              "Item Name": item.item_name || "—",
              "Narration": item.description || "—",
              "Account": this.getAccountName(item.account_id),
              "Amount (UGX)": Number(item.amount || 0),
            });
          });
        });

        rows.push({
          "Exp ID": "GRAND TOTAL",
          "Date": "",
          "Description": "",
          "Reference": "",
          "Trans #": "",
          "Item Name": "",
          "Narration": "",
          "Account": "",
          "Amount (UGX)": this.grandTotal,
        });

        const ws = XLSX.utils.json_to_sheet(rows);
        ws["!cols"] = [
          { wch: 10 }, { wch: 12 }, { wch: 35 }, { wch: 15 },
          { wch: 12 }, { wch: 28 }, { wch: 45 }, { wch: 30 }, { wch: 16 }
        ];

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Expense Details");
        XLSX.writeFile(wb, `expenses_${new Date().toISOString().slice(0,10)}.xlsx`);
      } catch (err) {
        console.error("Excel export failed:", err);
        alert("Failed to export to Excel.");
      }
    },

    exportPDF() {
      try {
        const doc = new jsPDF();

        doc.setFontSize(16);
        doc.text("Expense Report – Itemized Breakdown", 14, 18);

        doc.setFontSize(11);
        doc.text(`Period: ${this.dateRange.start} to ${this.dateRange.end}`, 14, 26);
        doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 32);

        const body = this.filteredExpenses.flatMap(exp =>
          exp.items.map(item => [
            exp.id,
            exp.expense_date,
            exp.description.length > 55 ? exp.description.substring(0, 52) + "..." : exp.description,
            exp.reference || "—",
            item.item_name,
            item.description?.length > 65 ? item.description.substring(0, 62) + "..." : (item.description || "—"),
            this.getAccountName(item.account_id),
            Number(item.amount).toLocaleString("en-US"),
          ])
        );

        doc.autoTable({
          head: [["ID", "Date", "Description", "Ref", "Item", "Narration", "Account", "Amount (UGX)"]],
          body,
          startY: 38,
          styles: { fontSize: 8, cellPadding: 3 },
          headStyles: { fillColor: [79, 70, 229], textColor: 255 },
          alternateRowStyles: { fillColor: [245, 247, 250] },
          columnStyles: {
            0: { cellWidth: 14 },
            1: { cellWidth: 22 },
            2: { cellWidth: 38 },
            3: { cellWidth: 16 },
            4: { cellWidth: 28 },
            5: { cellWidth: 45 },
            6: { cellWidth: 30 },
            7: { cellWidth: 24, halign: "right" },
          },
          margin: { top: 38, left: 14, right: 14 },
        });

        const finalY = doc.lastAutoTable.finalY + 10;
        doc.setFontSize(12);
        doc.setFont("helvetica", "bold");
        doc.text("Grand Total:", 140, finalY);
        doc.text(this.formatCurrency(this.grandTotal), 190, finalY, { align: "right" });

        doc.save(`expenses_detailed_${new Date().toISOString().slice(0,10)}.pdf`);
      } catch (err) {
        console.error("PDF export failed:", err);
        alert("Failed to export to PDF.");
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
  },
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

.group:hover .group-hover\:block {
  display: block;
}
</style>
