<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 sticky top-0 z-20">
    <!-- Mobile Menu Button & Logo (Visible on Mobile) -->
    <div class="flex items-center gap-2 md:hidden">
      <button 
        @click="$emit('toggle-menu')"
        class="p-2 hover:bg-gray-100 rounded-full"
      >
        <Menu :size="24" class="text-gray-600" />
      </button>
      <span class="text-lg font-bold text-gray-800 tracking-tight">Plover<span class="text-blue-600">Photos</span></span>
    </div>

    <!-- Search Bar -->
    <div class="flex-1 flex items-center px-4 md:px-8">
      <div class="relative group w-full">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search :size="20" class="text-gray-400 group-focus-within:text-blue-600 transition-colors" />
        </div>
        <input 
          v-model="searchQuery"
          @keyup.enter="handleSearch"
          type="text" 
          placeholder="搜索照片" 
          class="block w-full pl-10 pr-10 py-2.5 bg-gray-100 border-none rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all shadow-sm"
        >
        <button 
          v-if="searchQuery"
          @click="clearSearch"
          class="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer text-gray-400 hover:text-gray-600"
        >
          <X :size="16" />
        </button>
      </div>
    </div>

    <!-- Right Actions -->
    <div class="flex items-center gap-2">
      <input 
        type="file" 
        ref="fileInput" 
        multiple 
        accept="image/*,video/*" 
        class="hidden" 
        @change="handleFileUpload"
      >
      <button 
        @click="triggerUpload"
        class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
      >
        <Upload :size="18" />
        <span class="hidden sm:inline">上传</span>
      </button>
      

    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue';
import { usePhotoStore } from '../../stores/photo';
import { useUploadStore } from '../../stores/upload';
import { useRouter } from 'vue-router';
import { Search, Upload, Menu, X } from 'lucide-vue-next';

defineEmits(['toggle-menu']);

const photoStore = usePhotoStore();
const uploadStore = useUploadStore();
const router = useRouter();
const searchQuery = ref('');
const fileInput = ref(null);

const handleSearch = () => {
  if (searchQuery.value.trim()) {
      router.push({ name: 'search', query: { q: searchQuery.value } });
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  router.push({ name: 'home' }); // Or stay on search page with empty results?
};

const triggerUpload = () => {
  fileInput.value.click();
};

const handleFileUpload = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  
  uploadStore.addFiles(files);
  
  // Clear input
  event.target.value = '';
};


</script>
