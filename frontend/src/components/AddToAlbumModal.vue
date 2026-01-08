<script setup>
import { ref, onMounted } from 'vue'
import { useAlbumStore } from '../stores/album'
import { usePhotoStore } from '../stores/photo'
import { Plus, X, Image as ImageIcon } from 'lucide-vue-next'
import axios from 'axios'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close', 'added'])

const albumStore = useAlbumStore()
const photoStore = usePhotoStore()
const newAlbumName = ref('')
const creating = ref(false)
const adding = ref(false)

onMounted(() => {
  if (albumStore.albums.length === 0) {
    albumStore.fetchAlbums()
  }
})

const createAndAdd = async () => {
  if (!newAlbumName.value.trim()) return
  
  creating.value = true
  try {
    // 1. Create Album
    const res = await axios.post('/api/albums/', { name: newAlbumName.value })
    const newAlbum = res.data
    
    // 2. Add Photos
    await addToAlbum(newAlbum.id)
  } catch (e) {
    alert('创建相册失败')
    creating.value = false
  }
}

const addToAlbum = async (albumId) => {
  adding.value = true
  try {
    const photoIds = Array.from(photoStore.selectedPhotoIds)
    await axios.post(`/api/albums/${albumId}/add_photos/`, {
      photo_ids: photoIds
    })
    
    // Success
    emit('added')
    emit('close')
    photoStore.clearSelection()
    newAlbumName.value = ''
  } catch (e) {
    alert('添加照片失败')
  } finally {
    adding.value = false
    creating.value = false
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden flex flex-col max-h-[80vh]">
      <div class="p-4 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-bold text-gray-900">添加到相册</h3>
        <button @click="$emit('close')" class="p-2 hover:bg-gray-100 rounded-full text-gray-500">
          <X :size="20" />
        </button>
      </div>
      
      <div class="overflow-y-auto p-4 flex-1">
        <!-- Create New -->
        <div class="mb-4 pb-4 border-b border-gray-100">
            <div class="flex gap-2">
                <input 
                    v-model="newAlbumName"
                    type="text" 
                    placeholder="新建相册名称"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                    @keyup.enter="createAndAdd"
                >
                <button 
                    @click="createAndAdd"
                    :disabled="!newAlbumName.trim() || creating"
                    class="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                    <Plus :size="18" v-if="!creating" />
                    <span v-else class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin block"></span>
                </button>
            </div>
        </div>

        <!-- Existing Albums -->
        <div class="space-y-2">
            <div 
                v-for="album in albumStore.albums" 
                :key="album.id"
                @click="addToAlbum(album.id)"
                class="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors group"
            >
                <div class="w-12 h-12 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                    <img v-if="album.cover" :src="album.cover.thumbnail" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                        <ImageIcon :size="20" />
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <h4 class="font-medium text-gray-900 truncate">{{ album.name }}</h4>
                    <p class="text-xs text-gray-500">{{ album.photo_count }} 张照片</p>
                </div>
                <div class="opacity-0 group-hover:opacity-100 text-blue-600 font-medium text-sm transition-opacity">
                    添加
                </div>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>
