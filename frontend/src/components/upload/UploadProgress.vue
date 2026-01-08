<template>
  <div v-if="uploadStore.uploads.length > 0" class="fixed bottom-4 right-4 bg-white rounded-xl shadow-lg border border-gray-200 w-80 overflow-hidden z-50">
    <div class="bg-blue-50 px-4 py-3 flex items-center justify-between border-b border-blue-100">
      <div class="flex items-center gap-2">
        <UploadCloud v-if="uploadStore.isUploading" class="text-blue-600 animate-pulse" :size="18" />
        <CheckCircle v-else class="text-green-600" :size="18" />
        <span class="font-medium text-gray-800 text-sm">
            {{ uploadStore.isUploading ? '正在上传...' : '上传完成' }}
        </span>
      </div>
      <div class="flex items-center gap-2">
         <span class="text-xs font-mono text-gray-500">{{ completedCount }}/{{ totalCount }}</span>
         <button @click="isExpanded = !isExpanded" class="text-gray-400 hover:text-gray-600">
            <ChevronUp v-if="!isExpanded" :size="16" />
            <ChevronDown v-else :size="16" />
         </button>
         <button @click="uploadStore.clearCompleted" class="text-gray-400 hover:text-gray-600" title="清除已完成">
            <X :size="16" />
         </button>
      </div>
    </div>
    
    <!-- Progress Bar (Overall) -->
    <div class="h-1 bg-gray-100">
      <div class="h-full bg-blue-500 transition-all duration-300" :style="{ width: `${uploadStore.overallProgress}%` }"></div>
    </div>

    <!-- File List -->
    <div v-if="isExpanded" class="max-h-60 overflow-y-auto bg-white">
      <div v-for="file in uploadStore.uploads" :key="file.id" class="px-4 py-2 border-b border-gray-50 last:border-0 flex items-center gap-3">
        <div class="w-8 h-8 rounded bg-gray-100 flex items-center justify-center shrink-0">
          <FileImage class="text-gray-400" :size="16" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex justify-between mb-1">
            <div class="text-xs font-medium text-gray-700 truncate" :title="file.name">{{ file.name }}</div>
            <div class="text-xs" :class="statusColor(file.status)">{{ statusText(file) }}</div>
          </div>
          <div class="h-1 bg-gray-100 rounded-full overflow-hidden">
             <div class="h-full bg-blue-500 transition-all duration-300" 
                  :class="{ 'bg-red-500': file.status === 'error', 'bg-green-500': file.status === 'completed' }"
                  :style="{ width: `${file.progress}%` }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useUploadStore } from '../../stores/upload';
import { UploadCloud, CheckCircle, X, ChevronUp, ChevronDown, FileImage } from 'lucide-vue-next';

const uploadStore = useUploadStore();
const isExpanded = ref(true);

const totalCount = computed(() => uploadStore.uploads.length);
const completedCount = computed(() => uploadStore.uploads.filter(u => u.status === 'completed').length);

const statusColor = (status) => {
    switch (status) {
        case 'uploading': return 'text-blue-600';
        case 'completed': return 'text-green-600';
        case 'error': return 'text-red-500';
        default: return 'text-gray-400';
    }
}

const statusText = (file) => {
    if (file.status === 'error') return '失败';
    if (file.status === 'completed') return '完成';
    return `${file.progress}%`;
}
</script>
