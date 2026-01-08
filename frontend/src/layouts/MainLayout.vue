<template>
  <div 
    class="flex h-screen bg-white overflow-hidden relative"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <!-- Drag Overlay -->
    <div 
      v-if="isDragging" 
      class="absolute inset-0 z-50 bg-blue-500/10 backdrop-blur-sm border-4 border-blue-500 border-dashed m-4 rounded-xl flex items-center justify-center pointer-events-none"
    >
      <div class="bg-white p-6 rounded-xl shadow-2xl flex flex-col items-center gap-4">
        <Upload :size="48" class="text-blue-500" />
        <span class="text-xl font-bold text-gray-700">释放文件以上传</span>
      </div>
    </div>

    <!-- Sidebar Overlay for Mobile -->
    <div 
      v-if="isMobileMenuOpen" 
      class="fixed inset-0 bg-black/50 z-30 md:hidden"
      @click="isMobileMenuOpen = false"
    ></div>

    <Sidebar :class="{'translate-x-0': isMobileMenuOpen}" />
    
    <div class="flex-1 flex flex-col min-w-0">
      <TopBar @toggle-menu="isMobileMenuOpen = !isMobileMenuOpen" />
      <main class="flex-1 overflow-y-auto bg-white scroll-smooth flex flex-col">
        <div class="w-full flex-1 flex flex-col p-4 md:p-6 lg:p-8">
          <slot></slot>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue';
import Sidebar from '@/components/layout/Sidebar.vue';
import TopBar from '@/components/layout/TopBar.vue';
import { Upload } from 'lucide-vue-next';
import { useUploadStore } from '../stores/upload';

const isMobileMenuOpen = ref(false);
const isDragging = ref(false);
const uploadStore = useUploadStore();

const handleDrop = (e) => {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files && files.length > 0) {
    uploadStore.addFiles(files);
  }
};

// Provide it so components can close the menu
provide('closeMobileMenu', () => {
  isMobileMenuOpen.value = false;
});
</script>
