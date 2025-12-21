<template>
  <aside
    :class="[
      'bg-gray-800 text-white flex flex-col transition-all duration-300 ease-in-out',
      collapsed ? 'w-20' : 'w-64',
      isMobile ? (collapsed ? '-translate-x-full fixed z-40 h-full' : 'translate-x-0 fixed z-40 h-full') : 'static'
    ]"
  >
    <!-- Logo -->
    <div class="p-6 font-bold text-xl border-b border-gray-700 flex justify-between items-center">
      <span v-if="!collapsed">Retail Service Shop</span>
      <button @click="toggleSidebar" class="focus:outline-none">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </div>

    <!-- Menu -->
    <nav class="flex-1 mt-4 overflow-y-auto">
      <ul>
        <li v-for="item in filteredMenuItems" :key="item.name">
          <router-link
            :to="item.path"
            class="flex items-center px-6 py-3 hover:bg-gray-700 rounded gap-3 transition-colors"
            :class="{ 'bg-gray-700': isActive(item.path) }"
            @click="isMobile ? toggleSidebar() : null"
          >
            <span class="text-xl">{{ item.icon }}</span>
            <span v-if="!collapsed" class="whitespace-nowrap">{{ item.name }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Logout -->
    <div class="p-6 border-t border-gray-700">
      <button
        @click="logout"
        class="w-full bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-sm md:text-base"
      >
        Logout
      </button>
    </div>
  </aside>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api';

export default {
  props: {
    collapsed: Boolean,
    isMobile: Boolean,
    toggleSidebar: Function
  },
  setup(props) {
    const route = useRoute();
    const router = useRouter();

    const isActive = (path) => route.path === path;

    const logout = () => {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      if (api.defaults.headers.common['Authorization']) {
        delete api.defaults.headers.common['Authorization'];
      }
      router.push('/login');
    };

    // --- Load user permissions ---
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const permissions = user.permissions || [];
    console.log('User Permissions: ', permissions);
    console.log('User Role: ', user);

    // --- Full menu with associated permissions ---
    const menuItems = [
      { name: 'Dashboard', path: '/', icon: '🏠', permission: null },
      { name: 'Accounts', path: '/accounts', icon: '🏦', permission: 'view_ledger' },
      { name: 'Products', path: '/products', icon: '📦', permission: 'view_inventory' },
      { name: 'Customers', path: '/customers', icon: '👥', permission: 'view_customers' },
      { name: 'Enter Sale', path: '/sales', icon: '💰', permission: 'create_invoice' },
      { name: 'View Sales ', path: '/saleslist', icon: '📃', permission: 'view_invoices' },
      { name: 'Supplier', path: '/supplier', icon: '🚚', permission: 'view_suppliers' },
      { name: 'Enter Purchase', path: '/purchases', icon: '🛒', permission: 'create_purchase' },
      { name: 'View  Purchases', path: '/purchaselist', icon: '📋', permission: 'view_purchases' },
      { name: 'Expenses', path: '/expenses', icon: '💸', permission: 'view_expense' },
      { name: 'Reports', path: '/reports', icon: '📊', permission: 'view_reports' },
      { name: 'Users', path: '/users', icon: '👤', permission: 'view_users' },
    ];

    // --- Filter menu based on user permissions ---
    const filteredMenuItems = menuItems.filter(item => !item.permission || permissions.includes(item.permission));

    return { filteredMenuItems, isActive, logout };
  },
};
</script>

