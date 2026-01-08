<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { usePhotoStore } from '../stores/photo'
import axios from 'axios'
import PhotoGrid from '../components/PhotoGrid.vue'
import PhotoLightbox from '../components/PhotoLightbox.vue'
import AddToAlbumModal from '../components/AddToAlbumModal.vue'
import { Plus, X } from 'lucide-vue-next'

const photoStore = usePhotoStore()
const showAddToAlbum = ref(false)
let refreshInterval = null

const hasSelection = computed(() => photoStore.selectedPhotoIds.size > 0)

const checkScanningStatus = async () => {
  try {
    const response = await axios.get('/api/libraries/')
    const libraries = response.data.results || response.data
    const isScanning = libraries.some(lib => lib.scan_status === 'scanning')
    
    // 如果正在扫描，且没有定时任务，则启动定时任务
    if (isScanning && !refreshInterval) {
      refreshInterval = setInterval(() => {
        photoStore.fetchPhotos()
      }, 5000) // 每 5 秒刷新一次照片
    } else if (!isScanning && refreshInterval) {
      // 如果扫描结束，清除定时任务
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  } catch (e) {
    console.error('Failed to check scanning status', e)
  }
}

onMounted(() => {
  // 始终在进入页面时刷新一次，确保看到最新数据
  photoStore.fetchPhotos()
  
  // 检查扫描状态并启动轮询
  checkScanningStatus()
  // 每 10 秒检查一次扫描状态
  const statusCheckInterval = setInterval(checkScanningStatus, 10000)
  
  onUnmounted(() => {
    if (refreshInterval) clearInterval(refreshInterval)
    clearInterval(statusCheckInterval)
  })
})

const clearSelection = () => {
  photoStore.clearSelection()
}
</script>

<template>
  <div class="min-h-full pb-24"> <!-- Added padding-bottom for floating bar -->
    <PhotoGrid />
    <PhotoLightbox />
    
    <!-- Selection Floating Bar -->
    <div 
        v-if="hasSelection"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-white/90 backdrop-blur-md border border-gray-200 shadow-lg rounded-full px-6 py-3 flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-200"
    >
        <span class="text-sm font-medium text-gray-700 border-r border-gray-200 pr-4">
            已选择 {{ photoStore.selectedPhotoIds.size }} 张
        </span>
        
        <button 
            @click="showAddToAlbum = true"
            class="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
        >
            <Plus :size="18" />
            添加到相册
        </button>
        
        <button 
            @click="clearSelection"
            class="p-1 hover:bg-gray-100 rounded-full text-gray-500 transition-colors ml-2"
        >
            <X :size="18" />
        </button>
    </div>

    <AddToAlbumModal 
        :show="showAddToAlbum" 
        @close="showAddToAlbum = false"
    />
  </div>
</template>
