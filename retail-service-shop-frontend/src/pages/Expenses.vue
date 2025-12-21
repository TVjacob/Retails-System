<template>
  <div class="p-6 max-w-7xl mx-auto overflow-y-auto min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Expenses Management</h1>

    <!-- Sticky Toolbar: Filters & Actions -->
    <div class="sticky top-0 z-50 bg-white p-4 rounded-lg shadow-sm mb-4 flex flex-wrap gap-3 items-center">
      <div class="flex gap-2 items-center w-full md:w-auto">
        <input
          v-model="searchQuery"
          placeholder="Search description, reference, account or item..."
          @input="debouncedFetchExpenses"
          class="px-3 py-2 border rounded-lg w-64 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        />
        <input
          v-model="startDate"
          type="date"
          @change="fetchExpenses"
          class="px-3 py-2 border rounded-lg"
        />
        <input
          v-model="endDate"
          type="date"
          @change="fetchExpenses"
          class="px-3 py-2 border rounded-lg"
        />
      </div>

      <div class="ml-auto flex gap-2">
        <button
          @click="resetFilters"
          class="bg-gray-200 hover:bg-gray-300 px-3 py-2 rounded shadow-sm"
        >
          Reset
        </button>

        <button
          @click="showItemModal = true"
          class="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded shadow-sm"
        >
          + Add Expense Item
        </button>

        <button
          @click="showModal = true"
          class="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-2 rounded shadow-sm"
        >
          + Add Expense
        </button>

        <button
          @click="exportExcel"
          class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-2 rounded shadow-sm"
        >
          Export Excel
        </button>

        <button
          @click="exportPDF"
          class="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded shadow-sm"
        >
          Export PDF
        </button>
      </div>
    </div>

    <!-- Grand Total -->
    <div class="mb-4 p-4 bg-gray-50 rounded shadow-sm flex justify-between items-center">
      <div>
        <h2 class="text-lg font-bold">Grand Total Paid</h2>
        <p class="text-2xl font-semibold text-green-600">{{ formatNumber(grandTotal) }}</p>
      </div>

      <div class="text-sm text-gray-500">
        Showing <span class="font-medium">{{ expenses.length }}</span> records
      </div>
    </div>

    <!-- Expenses Table / Cards -->
    <div class="overflow-x-auto border rounded-lg shadow bg-white">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100 sticky top-[88px] z-40">
          <tr>
            <th class="p-3 border-b text-center w-12"></th>
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
            <tr class="transition-all duration-200 hover:bg-gray-50 cursor-pointer">
              <td class="p-3 text-center">
                <button @click="toggleExpand(expense.id, index)" class="text-indigo-600 font-bold">
                  {{ expandedRows.includes(expense.id) ? '−' : '+' }}
                </button>
              </td>

              <td class="p-3">{{ expense.id }}</td>
              <td class="p-3">{{ expense.description }}</td>
              <td class="p-3 text-right">{{ formatNumber(expense.total_amount) }}</td>
              <td class="p-3">{{ expense.reference }}</td>
              <td class="p-3">{{ formatDate(expense.expense_date) }}</td>
              <td class="p-3">{{ expense.transaction_no }}</td>

              <td class="p-3 text-center flex gap-2 justify-center">
                <button @click="editExpense(expense)" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded">
                  Edit
                </button>
                <button @click="deleteExpense(expense.id)" class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded">
                  Delete
                </button>
                <router-link :to="`/reports/expenses/${expense.id}`" class="text-indigo-600 underline">
                  View
                </router-link>
              </td>
            </tr>

            <!-- Expanded row with items -->
            <tr>
              <td colspan="8" class="p-0 border-t-0">
                <div :style="{ height: expandedRowHeights[expense.id] ? expandedRowHeights[expense.id] + 'px' : '0px' }" class="overflow-hidden transition-all duration-300">
                  <div class="p-4 bg-gray-50 border-t shadow-inner">
                    <div class="flex items-center justify-between mb-3">
                      <h3 class="font-semibold">Expense Items</h3>
                      <div class="text-sm text-gray-600">
                        Payment Account:
                        <span class="font-medium">{{ expense.payment_account || '—' }}</span>
                      </div>
                    </div>

                    <div class="overflow-x-auto">
                      <table class="w-full text-sm">
                        <thead>
                          <tr class="bg-gray-100">
                            <th class="p-2 border">Account</th>
                            <th class="p-2 border">Item Name</th>
                            <th class="p-2 border">Description</th>
                            <th class="p-2 border text-right">Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in expense.items" :key="item.id" class="hover:bg-white">
                            <td class="p-2 border">{{ item.account_name || getAccountName(item.account_id) || '—' }}</td>
                            <td class="p-2 border">{{ item.item_name }}</td>
                            <td class="p-2 border">{{ item.description }}</td>
                            <td class="p-2 border text-right">{{ formatNumber(item.amount) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                  </div>
                </div>
              </td>
            </tr>
          </template>

          <tr v-if="expenses.length === 0">
            <td colspan="8" class="p-6 text-center text-gray-500">No expenses found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- CREATE / EDIT EXPENSE MODAL -->
    <div v-if="showModal" class="fixed inset-0 flex items-start justify-center bg-black bg-opacity-50 z-[9999] p-6 overflow-y-auto">
      <div class="bg-white rounded-lg p-6 w-full max-w-[900px] relative shadow-xl">
        <h2 class="text-xl font-bold mb-3">{{ editingExpense ? 'Edit Expense' : 'Add Expense' }}</h2>
        <button @click="closeModal" class="absolute top-4 right-4 text-gray-600 hover:text-gray-900">✖</button>

        <!-- Header inputs -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <input v-model="expenseForm.description" placeholder="Expense Description" class="border p-2 rounded" />
          <input v-model="expenseForm.reference" placeholder="Reference" class="border p-2 rounded" />
          <input v-model="expenseForm.expense_date" type="date" class="border p-2 rounded" />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div class="col-span-1 md:col-span-2">
            <label class="text-sm text-gray-600">Payment Account</label>
            <input
              v-model="expenseForm.payment_account_name"
              placeholder="Type to search payment account (Cash/Bank)"
              @input="fetchCashBankAccounts(expenseForm.payment_account_name)"
              class="w-full border p-2 rounded"
              list="paymentAccounts"
            />
            <datalist id="paymentAccounts">
              <option v-for="acc in cashBankAccounts" :key="acc.id" :value="acc.name"></option>
            </datalist>
          </div>

          <div>
            <label class="text-sm text-gray-600">Transaction No</label>
            <input v-model="expenseForm.transaction_no" placeholder="Transaction No (optional)" class="w-full border p-2 rounded" />
          </div>
        </div>

        <!-- Items -->
        <h3 class="font-semibold mb-2">Expense Items</h3>

        <div v-for="(item, idx) in expenseForm.items" :key="idx" class="grid grid-cols-12 gap-2 items-end mb-2">
          <div class="col-span-12 md:col-span-3">
            <label class="text-xs text-gray-500">Expense Account</label>
            <input
              v-model="item.account_name"
              placeholder="Search expense account..."
              @input="fetchExpenseAccounts(item.account_name)"
              list="expenseAccounts"
              class="w-full border p-2 rounded"
            />
            <datalist id="expenseAccounts">
              <option v-for="acc in expenseAccounts" :key="acc.id" :value="acc.name"></option>
            </datalist>
          </div>

          <div class="col-span-12 md:col-span-3">
            <label class="text-xs text-gray-500">Item Name</label>
            <input v-model="item.item_name" placeholder="Item name" class="w-full border p-2 rounded" />
          </div>

          <div class="col-span-12 md:col-span-4">
            <label class="text-xs text-gray-500">Description</label>
            <input v-model="item.description" placeholder="Description" class="w-full border p-2 rounded" />
          </div>

          <div class="col-span-8 md:col-span-1">
            <label class="text-xs text-gray-500">Amount</label>
            <input v-model.number="item.amount" type="number" placeholder="0.00" class="w-full border p-2 rounded text-right" />
          </div>

          <div class="col-span-4 md:col-span-1 text-right">
            <button type="button" @click="removeItem(idx)" class="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded">
              ✖
            </button>
          </div>
        </div>

        <div class="mb-4">
          <button type="button" @click="addItem" class="bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded">+ Add Item</button>
        </div>

        <!-- Amount Paid (preview) -->
        <div class="mb-4">
          <label class="block text-sm font-bold mb-1">Amount (sum of items)</label>
          <input :value="formatNumber(amountPaid)" class="border p-2 rounded w-full bg-gray-50 text-right" disabled />
        </div>

        <div class="flex justify-end gap-2">
          <button @click="closeModal" class="px-4 py-2 rounded border">Cancel</button>
          <button @click="submitExpense" class="px-5 py-2 rounded bg-indigo-600 text-white"> {{ editingExpense ? 'Update' : 'Create' }} </button>
        </div>
      </div>
    </div>

    <!-- Add Expense Item Modal -->
    <div v-if="showItemModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-[9999] p-6">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h2 class="text-xl font-bold mb-3">Add Expense Item</h2>
        <button class="absolute top-4 right-4" @click="closeItemModal">✖</button>

        <div class="grid gap-3 mb-4">
          <input v-model="expenseItemForm.name" placeholder="Expense Item Name" class="border p-2 rounded" />
          <select v-model="expenseItemForm.account_subtype" class="border p-2 rounded">
            <option value="">Select Expense Type</option>
            <option v-for="acc in expenseSubtypes" :key="acc" :value="acc">{{ acc }}</option>
          </select>
        </div>

        <div class="flex justify-end">
          <button @click="submitExpenseItem" class="bg-indigo-600 text-white px-4 py-2 rounded">Save Item</button>
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
import debounce from "lodash.debounce";

export default {
  name: "ExpensesManagement",
  data() {
    const today = new Date().toISOString().split("T")[0];
    return {
      expenses: [],
      searchQuery: "",
      startDate: today,
      endDate: today,
      showModal: false,
      editingExpense: false,
      expandedRows: [],
      expandedRowHeights: {},
      expenseForm: {
        id: null,
        description: "",
        payment_account_name: "",
        payment_account_id: null,
        expense_date: today,
        reference: "",
        transaction_no: "",
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
      return this.expenses.reduce((sum, expense) => sum + (Number(expense.total_amount) || 0), 0);
    },
    amountPaid() {
      return this.expenseForm.items.reduce((total, item) => total + (Number(item.amount) || 0), 0);
    },
  },
  methods: {
    // ---- formatting helpers ----
    formatNumber(num) {
      return Number(num || 0).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    },
    formatDate(dateStr) {
      if (!dateStr) return "";
      const d = new Date(dateStr);
      return d.toLocaleDateString();
    },

    // ---- fetchers ----
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
        this.expenseSubtypes = [
          ...new Set(res.data.filter((a) => a.account_type === "EXPENSE").map((a) => a.account_subtype)),
        ];
      } catch (err) {
        console.error("Error fetching expense subtypes:", err);
      }
    },

    // ---- expenses list ----
    async fetchExpenses() {
      try {
        const res = await api.get("/expenses/", {
          params: {
            start_date: this.startDate || undefined,
            end_date: this.endDate || undefined,
            search: this.searchQuery || undefined,
          },
        });
        // normalize incoming data a bit in case items don't include account_name
        this.expenses = (res.data || []).map((e) => {
          return {
            ...e,
            payment_account: e.payment_account || (e.payment_account_name ? e.payment_account_name : null),
            items: (e.items || []).map((it) => ({
              ...it,
              account_name: it.account_name || null,
            })),
          };
        });
        this.$nextTick(() => this.updateExpandedHeights());
      } catch (err) {
        console.error("Error fetching expenses:", err);
        alert("Failed to load expenses. See console for details.");
      }
    },

    debouncedFetchExpenses: debounce(function () {
      this.fetchExpenses();
    }, 450),

    // ---- table helpers & expand/collapse ----
    toggleExpand(id, index) {
      const pos = this.expandedRows.indexOf(id);
      if (pos > -1) this.expandedRows.splice(pos, 1);
      else this.expandedRows.push(id);
      this.$nextTick(() => this.updateExpandedHeights());
    },
    updateExpandedHeights() {
      // attempt to set heights for animated expansion
      // we rely on $refs.expandedRowsRefs being an array corresponding to table expanded rows
      const rows = this.$refs.expandedRowsRefs;
      if (!rows) return;
      // if it's a NodeList/Array, map them to expenses by index
      this.expenses.forEach((exp, idx) => {
        const el = rows[idx];
        if (el) {
          // el is the <div> wrapper; if its content is visible, record the scrollHeight
          this.expandedRowHeights = {
            ...this.expandedRowHeights,
            [exp.id]: this.expandedRows.includes(exp.id) ? el.scrollHeight : 0,
          };
        }
      });
    },

    // ---- CRUD: Create / Update / Delete expense ----
    addItem() {
      this.expenseForm.items.push({ account_name: "", account_id: null, item_name: "", description: "", amount: 0 });
    },
    removeItem(index) {
      this.expenseForm.items.splice(index, 1);
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
        transaction_no: "",
        items: [{ account_name: "", account_id: null, item_name: "", description: "", amount: 0 }],
      };
      this.editingExpense = false;
    },

    async submitExpense() {
      // map payment account name to id
      const paymentAcc = this.cashBankAccounts.find((a) => a.name === this.expenseForm.payment_account_name);
      if (!paymentAcc) {
        alert("Please select or type an existing Cash/Bank account from the list.");
        return;
      }
      this.expenseForm.payment_account_id = paymentAcc.id;

      // map each item account name to id
      for (const item of this.expenseForm.items) {
        const acc = this.expenseAccounts.find((a) => a.name === item.account_name);
        if (!acc) {
          alert(`Invalid expense account for item "${item.item_name}". Please select account from list.`);
          return;
        }
        item.account_id = acc.id;
      }

      // basic validations
      if (!this.expenseForm.description.trim()) {
        alert("Expense description is required.");
        return;
      }
      if (!this.expenseForm.expense_date) {
        alert("Expense date is required.");
        return;
      }
      if (!this.expenseForm.items.length) {
        alert("Add at least one expense item.");
        return;
      }

      try {
        if (this.editingExpense && this.expenseForm.id) {
          await api.put(`/expenses/${this.expenseForm.id}`, this.expenseForm);
          alert("Expense updated.");
        } else {
          await api.post("/expenses/", this.expenseForm);
          alert("Expense created.");
        }
        this.closeModal();
        await this.fetchExpenses();
      } catch (err) {
        console.error("Error submitting expense:", err);
        alert("Failed to submit expense. See console for details.");
      }
    },

    editExpense(expense) {
      this.expenseForm = {
        id: expense.id,
        description: expense.description,
        payment_account_name: expense.payment_account || this.cashBankAccounts.find((a) => a.id === expense.payment_account_id)?.name || "",
        payment_account_id: expense.payment_account_id,
        expense_date: expense.expense_date ? expense.expense_date.split("T")[0] : new Date().toISOString().split("T")[0],
        reference: expense.reference || "",
        transaction_no: expense.transaction_no || "",
        items: (expense.items || []).map((i) => ({
          account_name: i.account_name || this.getAccountName(i.account_id) || "",
          account_id: i.account_id,
          item_name: i.item_name,
          description: i.description,
          amount: i.amount,
        })),
      };
      this.editingExpense = true;
      this.showModal = true;
    },

    async deleteExpense(id) {
      if (!confirm("Delete this expense?")) return;
      try {
        await api.delete(`/expenses/${id}`);
        alert("Deleted.");
        this.fetchExpenses();
      } catch (err) {
        console.error("Error deleting expense:", err);
        alert("Delete failed. See console.");
      }
    },

    // ---- expense item modal ----
    closeItemModal() {
      this.showItemModal = false;
    },
    async submitExpenseItem() {
      if (!this.expenseItemForm.name.trim() || !this.expenseItemForm.account_subtype) {
        alert("Please fill required fields for expense item.");
        return;
      }
      try {
        const res = await api.post("/accounts/expense-items", {
          name: this.expenseItemForm.name.trim(),
          account_subtype: this.expenseItemForm.account_subtype,
        });
        alert(res.data?.message || "Expense item created");
        this.expenseItemForm = { name: "", account_subtype: "" };
        this.showItemModal = false;
        await this.fetchExpenseAccounts();
      } catch (err) {
        console.error("Error creating expense item:", err);
        alert("Failed to create expense item.");
      }
    },

    // ---- helpers ----
    getAccountName(accountId) {
      const acc = this.expenseAccounts.find((a) => a.id === accountId);
      return acc ? acc.name : null;
    },

    // ---- exports ----
    exportExcel() {
      try {
        const ws = XLSX.utils.json_to_sheet(this.expenses);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Expenses");
        XLSX.writeFile(wb, `expenses-${new Date().toISOString().slice(0,10)}.xlsx`);
      } catch (err) {
        console.error("Export Excel failed:", err);
        alert("Export failed.");
      }
    },
    exportPDF() {
      try {
        const doc = new jsPDF();
        doc.autoTable({
          head: [["ID", "Description", "Total Amount", "Reference", "Expense Date", "Transaction No"]],
          body: this.expenses.map((e) => [
            e.id,
            e.description,
            this.formatNumber(e.total_amount),
            e.reference,
            this.formatDate(e.expense_date),
            e.transaction_no,
          ]),
        });
        doc.save(`expenses-${new Date().toISOString().slice(0,10)}.pdf`);
      } catch (err) {
        console.error("Export PDF failed:", err);
        alert("Export failed.");
      }
    },

    resetFilters() {
      const today = new Date().toISOString().split("T")[0];
      this.searchQuery = "";
      this.startDate = today;
      this.endDate = today;
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
/* animations */
.animate-fadeIn { animation: fadeIn 0.45s ease-in-out both; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-6px);} to { opacity: 1; transform: translateY(0);} }

/* modern card-like table look */
table { border-spacing: 0; }
thead th { font-size: 12px; color: #4b5563; letter-spacing: 0.02em; }
tbody tr td { font-size: 14px; color: #374151; }

/* responsive adjustments */
@media (max-width: 768px) {
  .sticky { position: sticky; top: 0; }
}

/* keep modal visible above everything */
.fixed { -webkit-overflow-scrolling: touch; }

/* small cosmetic helpers */
.bg-gray-50 { background-color: #f9fafb; }
</style>
