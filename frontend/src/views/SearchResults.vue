<template>
  <div class="h-full flex flex-col bg-white">
    <div class="p-6 border-b border-gray-100">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">搜索结果</h1>
      <p class="text-gray-500">"{{ query }}" 的搜索结果 ({{ photoStore.count }} 张)</p>
    </div>
    
    <div class="flex-1 overflow-y-auto px-6">
        <div v-if="photoStore.error" class="text-center py-12 text-red-500">
            <p>{{ photoStore.error }}</p>
            <button @click="photoStore.searchPhotos(query)" class="mt-4 text-blue-500 hover:underline">重试</button>
        </div>
        <PhotoGrid v-else />
    </div>
    
    <PhotoLightbox />
  </div>
</template>

<script setup>
import { onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePhotoStore } from '../stores/photo'
import PhotoGrid from '../components/PhotoGrid.vue'
import PhotoLightbox from '../components/PhotoLightbox.vue'

const route = useRoute()
const photoStore = usePhotoStore()

const query = computed(() => route.query.q || '')

onMounted(() => {
    if (query.value) {
        photoStore.searchPhotos(query.value)
    }
})

watch(query, (newQuery) => {
    if (newQuery) {
        photoStore.searchPhotos(newQuery)
    }
})
</script>