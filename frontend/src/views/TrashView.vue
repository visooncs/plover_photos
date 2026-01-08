<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { usePhotoStore } from '../stores/photo'
import PhotoGrid from '../components/PhotoGrid.vue'
import PhotoLightbox from '../components/PhotoLightbox.vue'
import { Trash2, RefreshCw, X, AlertTriangle } from 'lucide-vue-next'

const photoStore = usePhotoStore()
const loading = ref(false)

const hasSelection = computed(() => photoStore.selectedPhotoIds.size > 0)

onMounted(() => {
  photoStore.isTrashMode = true
  photoStore.clearPhotos()
  photoStore.fetchPhotos('/api/photos/trash/')
})

onUnmounted(() => {
  photoStore.isTrashMode = false
  photoStore.clearPhotos() // Clear trash photos so they don't flash on home
})

const clearSelection = () => {
  photoStore.clearSelection()
}

const handleEmptyTrash = async () => {
  if (!confirm('确定要清空回收站吗？此操作不可恢复。')) return
  try {
    await photoStore.emptyTrash()
    alert('回收站已清空')
  } catch (e) {
    alert('清空失败')
  }
}

const handleRestoreSelection = async () => {
  // if (!confirm(`确定要恢复选中的 ${photoStore.selectedPhotoIds.size} 张照片吗？`)) return
  
  const ids = Array.from(photoStore.selectedPhotoIds)
  // Process sequentially or Promise.all. Promise.all might overwhelm if many.
  // API doesn't support batch restore yet, but loop is fine for now.
  let successCount = 0
  for (const id of ids) {
      try {
          await photoStore.restorePhoto(id)
          successCount++
      } catch (e) {
          console.error(`Failed to restore ${id}`, e)
      }
  }
  photoStore.clearSelection()
  alert(`已恢复 ${successCount} 张照片`)
}

const handlePermanentDeleteSelection = async () => {
  if (!confirm(`确定要永久删除选中的 ${photoStore.selectedPhotoIds.size} 张照片吗？此操作不可恢复！`)) return
  
  const ids = Array.from(photoStore.selectedPhotoIds)
  let successCount = 0
  for (const id of ids) {
      try {
          await photoStore.permanentDeletePhoto(id)
          successCount++
      } catch (e) {
          console.error(`Failed to delete ${id}`, e)
      }
  }
  photoStore.clearSelection()
  alert(`已永久删除 ${successCount} 张照片`)
}
</script>

<template>
  <div class="min-h-full pb-24">
    <div class="px-4 py-6 sm:px-8 flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Trash2 class="text-gray-500" />
                回收站
            </h1>
            <p class="text-gray-500 mt-1 text-sm">照片会在删除 30 天后自动清除</p>
        </div>
        
        <button 
            v-if="photoStore.count > 0"
            @click="handleEmptyTrash"
            class="px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors flex items-center gap-2"
        >
            <Trash2 :size="16" />
            清空回收站
        </button>
    </div>

    <div v-if="photoStore.count === 0 && !photoStore.loading" class="flex flex-col items-center justify-center py-20 text-gray-400">
        <Trash2 :size="64" class="mb-4 opacity-20" />
        <p>回收站是空的</p>
    </div>

    <PhotoGrid />
    <PhotoLightbox />
    
    <!-- Selection Floating Bar (Trash Mode) -->
    <div 
        v-if="hasSelection"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-white/90 backdrop-blur-md border border-gray-200 shadow-lg rounded-full px-6 py-3 flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-200"
    >
        <span class="text-sm font-medium text-gray-700 border-r border-gray-200 pr-4">
            已选择 {{ photoStore.selectedPhotoIds.size }} 张
        </span>
        
        <button 
            @click="handleRestoreSelection"
            class="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
        >
            <RefreshCw :size="18" />
            恢复
        </button>
        
        <button 
            @click="handlePermanentDeleteSelection"
            class="flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-700 transition-colors ml-2"
        >
            <AlertTriangle :size="18" />
            永久删除
        </button>
        
        <button 
            @click="clearSelection"
            class="p-1 hover:bg-gray-100 rounded-full text-gray-500 transition-colors ml-2"
        >
            <X :size="18" />
        </button>
    </div>
  </div>
</template>
