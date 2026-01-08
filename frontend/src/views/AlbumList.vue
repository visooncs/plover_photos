<script setup>
import { onMounted, ref } from 'vue'
import { useAlbumStore } from '../stores/album'
import { useRouter } from 'vue-router'
import { Image, Plus } from 'lucide-vue-next'
import axios from 'axios'

const albumStore = useAlbumStore()
const router = useRouter()
const showCreateModal = ref(false)
const newAlbumName = ref('')
const creating = ref(false)

onMounted(() => {
  albumStore.fetchAlbums()
})

const openAlbum = (id) => {
  router.push({ name: 'album-detail', params: { id } })
}

const createAlbum = async () => {
  if (!newAlbumName.value.trim()) return
  
  creating.value = true
  try {
    const response = await axios.post('/api/albums/', {
      name: newAlbumName.value
    })
    newAlbumName.value = ''
    showCreateModal.value = false
    // Refresh list
    albumStore.fetchAlbums()
    // Navigate to new album
    openAlbum(response.data.id)
  } catch (e) {
    alert('创建相册失败')
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <div class="p-6 border-b border-gray-100 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">所有相册</h1>
    </div>
    
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="albumStore.error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {{ albumStore.error }}
      </div>

      <div v-if="albumStore.loading && albumStore.albums.length === 0" class="flex justify-center h-64 items-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>

      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-6 pb-8">
        <!-- Create Album Card -->
        <div 
          @click="showCreateModal = true"
          class="aspect-square bg-gray-50 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-gray-100 transition-colors border-2 border-dashed border-gray-300 hover:border-blue-400 group"
        >
          <div class="w-12 h-12 rounded-full bg-white flex items-center justify-center shadow-sm mb-3 group-hover:scale-110 transition-transform">
              <Plus :size="24" class="text-blue-600" />
          </div>
          <span class="text-sm font-medium text-gray-600 group-hover:text-blue-600 transition-colors">新建相册</span>
        </div>

        <div 
          v-for="album in albumStore.albums" 
          :key="album.id"
          class="group cursor-pointer"
          @click="openAlbum(album.id)"
        >
          <div class="aspect-square rounded-xl overflow-hidden bg-gray-100 mb-2 relative shadow-sm group-hover:shadow-md transition-shadow">
            <img 
              v-if="album.cover" 
              :src="album.cover.thumbnail" 
              :alt="album.name"
              class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
            <div v-else class="w-full h-full flex items-center justify-center bg-gray-200">
              <Image :size="32" class="text-gray-400" />
            </div>
          </div>
          <h3 class="font-medium text-gray-900 truncate">{{ album.name }}</h3>
          <p class="text-sm text-gray-500">{{ album.photo_count }} 张照片</p>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden">
            <div class="p-6">
                <h3 class="text-lg font-bold text-gray-900 mb-4">新建相册</h3>
                <input 
                    ref="nameInput"
                    v-model="newAlbumName"
                    type="text" 
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    placeholder="相册名称"
                    @keyup.enter="createAlbum"
                    autofocus
                >
            </div>
            <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3">
                <button 
                    @click="showCreateModal = false"
                    class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    取消
                </button>
                <button 
                    @click="createAlbum"
                    :disabled="creating || !newAlbumName.trim()"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    创建
                </button>
            </div>
        </div>
    </div>
  </div>
</template>
