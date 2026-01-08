<script setup>
import { onMounted, onUnmounted, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePhotoStore } from '../stores/photo'
import PhotoGrid from '../components/PhotoGrid.vue'
import PhotoLightbox from '../components/PhotoLightbox.vue'
import { ArrowLeft, Clock } from 'lucide-vue-next'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const photoStore = usePhotoStore()

const memory = ref(null)
const loading = ref(false)

const loadData = async () => {
    const memoryId = route.params.id
    if (memoryId) {
        loading.value = true
        try {
            // Fetch Memory Details
            const res = await axios.get(`/api/memories/${memoryId}/`)
            memory.value = res.data
            
            // Fetch Memory Photos
            photoStore.clearPhotos()
            // Using the custom action endpoint
            await photoStore.fetchPhotos(`/api/memories/${memoryId}/photos/`)
        } catch (e) {
            console.error("Failed to load memory", e)
        } finally {
            loading.value = false
        }
    }
}

onMounted(() => {
    loadData()
})

watch(() => route.params.id, (newId) => {
    if (newId) loadData()
})

onUnmounted(() => {
    photoStore.clearPhotos()
})
</script>

<template>
  <div class="min-h-full bg-white">
    <!-- Header -->
    <div class="pt-20 px-4 sm:px-8 pb-4 border-b border-gray-100 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4 flex-1 min-w-0">
            <router-link to="/albums" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
                <ArrowLeft :size="24" class="text-gray-600" />
            </router-link>
            
            <div v-if="memory" class="min-w-0 flex items-center gap-3">
                <div class="p-2 bg-blue-50 text-blue-600 rounded-full">
                    <Clock :size="20" />
                </div>
                <div>
                    <h1 class="text-2xl font-bold text-gray-900 truncate">{{ memory.title }}</h1>
                    <p class="text-gray-500 text-sm mt-1 truncate" v-if="memory.description">
                        {{ memory.description }}
                    </p>
                </div>
            </div>
            <div v-else-if="loading" class="h-10 w-48 bg-gray-200 animate-pulse rounded"></div>
        </div>
    </div>

    <!-- Photos -->
    <PhotoGrid :is-selection-mode="false" />
    <PhotoLightbox />
  </div>
</template>
