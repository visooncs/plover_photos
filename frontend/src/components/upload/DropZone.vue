<template>
  <div 
    class="fixed inset-0 z-[100] bg-blue-500/20 backdrop-blur-sm flex items-center justify-center transition-opacity duration-300"
    :class="{ 'opacity-0 pointer-events-none': !isDragging, 'opacity-100': isDragging }"
    @dragenter.prevent
    @dragover.prevent
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <div class="bg-white/90 p-12 rounded-3xl shadow-2xl text-center border-4 border-blue-400 border-dashed">
      <div class="bg-blue-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6">
        <UploadCloud class="text-blue-600" :size="48" />
      </div>
      <h3 class="text-2xl font-bold text-gray-800 mb-2">释放以上传照片</h3>
      <p class="text-gray-500">支持多文件批量上传</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useUploadStore } from '../../stores/upload';
import { UploadCloud } from 'lucide-vue-next';

const uploadStore = useUploadStore();
const isDragging = ref(false);
let dragCounter = 0;

const onDragEnter = (e) => {
  e.preventDefault();
  dragCounter++;
  if (e.dataTransfer.types.includes('Files')) {
    isDragging.value = true;
  }
};

const onDragLeave = (e) => {
  e.preventDefault();
  dragCounter--;
  if (dragCounter === 0) {
    isDragging.value = false;
  }
};

const onDrop = (e) => {
  e.preventDefault();
  isDragging.value = false;
  dragCounter = 0;
  
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    uploadStore.addFiles(e.dataTransfer.files);
  }
};

onMounted(() => {
  window.addEventListener('dragenter', onDragEnter);
  window.addEventListener('dragover', (e) => e.preventDefault());
  window.addEventListener('dragleave', onDragLeave);
  window.addEventListener('drop', onDrop);
});

onUnmounted(() => {
  window.removeEventListener('dragenter', onDragEnter);
  window.removeEventListener('dragover', (e) => e.preventDefault());
  window.removeEventListener('dragleave', onDragLeave);
  window.removeEventListener('drop', onDrop);
});
</script>
