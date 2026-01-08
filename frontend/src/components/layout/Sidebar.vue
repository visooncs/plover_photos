<template>
  <aside class="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0 fixed inset-y-0 left-0 z-40 transform -translate-x-full md:relative md:translate-x-0 transition-transform duration-300 ease-in-out">
    <!-- Logo -->
    <div class="h-16 flex items-center px-6">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-image"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
        </div>
        <span class="text-xl font-bold text-gray-800 tracking-tight">Plover<span class="text-blue-600">Photos</span></span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-2 space-y-1 overflow-y-auto" @click="closeMobileMenu">
      <router-link to="/" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <Image :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>照片</span>
        </a>
      </router-link>
      
      <router-link to="/explore" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <Search :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>探索</span>
        </a>
      </router-link>
      
      <router-link to="/albums" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <Album :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>相册</span>
        </a>
      </router-link>

      <router-link to="/people" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <User :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>人物</span>
        </a>
      </router-link>

      <router-link to="/places" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <Map :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>地点</span>
        </a>
      </router-link>

      <div class="my-4 border-t border-gray-200 mx-4"></div>

      <router-link to="/libraries" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <FolderCog :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>库管理</span>
        </a>
      </router-link>

      <router-link to="/maintenance" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <Settings :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>系统维护</span>
        </a>
      </router-link>

      <router-link to="/trash" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center gap-4 px-4 py-3 rounded-full transition-colors', isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100']">
          <Trash2 :class="['w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-500']" />
          <span>回收站</span>
        </a>
      </router-link>
    </nav>

    <!-- Storage Info -->
    <div class="p-6 border-t border-gray-200" v-if="storageInfo">
      <div class="flex items-center gap-2 text-sm text-gray-600 mb-2">
        <Cloud :size="16" />
        <span>存储空间</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-1.5 mb-2">
        <div class="bg-blue-600 h-1.5 rounded-full" :style="{ width: usagePercentage + '%' }"></div>
      </div>
      <div class="text-xs text-gray-500">已使用 {{ formatBytes(storageInfo.used_bytes) }} (共 {{ formatBytes(storageInfo.disk_total) }})</div>
    </div>
  </aside>
</template>

<script setup>
import { Image, Search, Album, User, Trash2, Cloud, Map, FolderCog, Settings } from 'lucide-vue-next';
import { ref, onMounted, computed, inject } from 'vue';

const closeMobileMenu = inject('closeMobileMenu');
const storageInfo = ref(null);

const fetchStorageInfo = async () => {
  try {
    const response = await fetch('/api/system/storage/');
    if (response.ok) {
      storageInfo.value = await response.json();
    }
  } catch (error) {
    console.error('Failed to fetch storage info:', error);
  }
};

const usagePercentage = computed(() => {
  if (!storageInfo.value || !storageInfo.value.disk_total) return 0;
  // Calculate percentage of disk used (by everything, not just photos, as returned by shutil.disk_usage)
  // Or should we show photo usage vs total disk?
  // The user asked for "current photo occupied total space and disk remaining space"
  // Let's assume the progress bar shows total disk usage to be safe, or just photo usage?
  // Usually cloud storage shows quota. Here it's local disk.
  // Let's show photo usage vs total disk for the text, but the bar might be misleading if we only show photo usage on a full disk.
  // Let's stick to disk usage for the bar (disk_used / disk_total) to warn about full disk.
  return (storageInfo.value.disk_used / storageInfo.value.disk_total) * 100;
});

function formatBytes(bytes, decimals = 1) {
  if (!bytes) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

onMounted(() => {
  fetchStorageInfo();
});
</script>
