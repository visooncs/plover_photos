<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAlbumStore } from '../stores/album'
import { usePhotoStore } from '../stores/photo'
import PhotoGrid from '../components/PhotoGrid.vue'
import PhotoLightbox from '../components/PhotoLightbox.vue'
import { ArrowLeft, Edit2, Trash2, X, CheckSquare, Image as ImageIcon } from 'lucide-vue-next'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const albumStore = useAlbumStore()
const photoStore = usePhotoStore()

const showEditModal = ref(false)
const editName = ref('')
const editing = ref(false)
const isSelectionMode = ref(false)
const removing = ref(false)

const loadData = async () => {
    const albumId = route.params.id
    if (albumId) {
        // Fetch Album Details
        await albumStore.fetchAlbum(albumId)
        
        // Fetch Album Photos
        photoStore.clearPhotos()
        await photoStore.fetchPhotos('/api/photos/', { albums: albumId })
    }
}

onMounted(() => {
    loadData()
})

// Watch for route changes (e.g. switching albums directly)
watch(() => route.params.id, (newId) => {
    if (newId) loadData()
})

onUnmounted(() => {
    photoStore.clearPhotos()
    photoStore.clearSelection()
})

const openEditModal = () => {
    if (!albumStore.currentAlbum) return
    editName.value = albumStore.currentAlbum.name
    showEditModal.value = true
}

const updateAlbum = async () => {
    if (!editName.value.trim()) return
    editing.value = true
    try {
        await axios.patch(`/api/albums/${route.params.id}/`, {
            name: editName.value
        })
        showEditModal.value = false
        // Refresh album details
        albumStore.fetchAlbum(route.params.id)
    } catch (e) {
        alert('更新失败')
    } finally {
        editing.value = false
    }
}

const deleteAlbum = async () => {
    if (!confirm('确定要删除这个相册吗？照片本身不会被删除。')) return
    try {
        await axios.delete(`/api/albums/${route.params.id}/`)
        router.push('/albums')
    } catch (e) {
        alert('删除失败')
    }
}

const toggleSelectionMode = () => {
    isSelectionMode.value = !isSelectionMode.value
    if (!isSelectionMode.value) {
        photoStore.clearSelection()
    }
}

const removeSelectedPhotos = async () => {
    const selectedIds = Array.from(photoStore.selectedPhotoIds)
    if (selectedIds.length === 0) return
    
    // if (!confirm(`确定要从相册移除选中的 ${selectedIds.length} 张照片吗？`)) return

    removing.value = true
    try {
        await axios.post(`/api/albums/${route.params.id}/remove_photos/`, {
            photo_ids: selectedIds
        })
        photoStore.clearSelection()
        isSelectionMode.value = false
        // Reload photos
        loadData()
    } catch (e) {
        alert('移除失败')
    } finally {
        removing.value = false
    }
}
</script>

<template>
  <div class="min-h-full bg-white">
    <!-- Header -->
    <div class="pt-20 px-4 sm:px-8 pb-4 border-b border-gray-100 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4 flex-1 min-w-0">
            <router-link to="/albums" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
                <ArrowLeft :size="24" class="text-gray-600" />
            </router-link>
            
            <div v-if="albumStore.currentAlbum" class="min-w-0">
                <h1 class="text-2xl font-bold text-gray-900 truncate">{{ albumStore.currentAlbum.name }}</h1>
                <p class="text-gray-500 text-sm mt-1 truncate" v-if="albumStore.currentAlbum.description">
                    {{ albumStore.currentAlbum.description }}
                </p>
                <p class="text-gray-400 text-xs mt-1">
                    {{ albumStore.currentAlbum.photo_count }} 张照片
                </p>
            </div>
            <div v-else-if="albumStore.loading" class="h-10 w-48 bg-gray-200 animate-pulse rounded"></div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2" v-if="albumStore.currentAlbum">
            <template v-if="isSelectionMode">
                <button 
                    v-if="photoStore.selectedPhotoIds.size === 1"
                    @click="setAsCover"
                    class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="设为封面"
                >
                    <ImageIcon :size="20" />
                </button>
                <button 
                    @click="removeSelectedPhotos"
                    :disabled="photoStore.selectedPhotoIds.size === 0 || removing"
                    class="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    移除 ({{ photoStore.selectedPhotoIds.size }})
                </button>
                <button 
                    @click="toggleSelectionMode"
                    class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="取消选择"
                >
                    <X :size="20" />
                </button>
            </template>
            <template v-else>
                <button 
                    @click="toggleSelectionMode"
                    class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="管理照片"
                >
                    <CheckSquare :size="20" />
                </button>
                <button 
                    @click="openEditModal"
                    class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="重命名相册"
                >
                    <Edit2 :size="20" />
                </button>
                <button 
                    @click="deleteAlbum"
                    class="p-2 text-gray-600 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
                    title="删除相册"
                >
                    <Trash2 :size="20" />
                </button>
            </template>
        </div>
    </div>

    <!-- Photos -->
    <PhotoGrid :is-selection-mode="isSelectionMode" />
    <PhotoLightbox />

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden">
            <div class="p-6">
                <h3 class="text-lg font-bold text-gray-900 mb-4">重命名相册</h3>
                <input 
                    v-model="editName"
                    type="text" 
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    placeholder="相册名称"
                    @keyup.enter="updateAlbum"
                    autofocus
                >
            </div>
            <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3">
                <button 
                    @click="showEditModal = false"
                    class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    取消
                </button>
                <button 
                    @click="updateAlbum"
                    :disabled="editing || !editName.trim()"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    保存
                </button>
            </div>
        </div>
    </div>
  </div>
</template>
