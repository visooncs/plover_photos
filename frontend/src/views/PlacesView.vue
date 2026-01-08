<template>
  <div class="h-full flex flex-col bg-white">
    <div class="p-6 border-b border-gray-100 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">地点</h1>
      <div class="text-sm text-gray-500">共 {{ places.length }} 个地点</div>
    </div>
    
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
      
      <div v-else-if="places.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-500">
        <MapPin class="w-16 h-16 mb-4 text-gray-300" />
        <p class="text-lg">暂无地点信息</p>
        <p class="text-sm mt-2">当照片包含 GPS 信息时，这里会自动显示地点。</p>
      </div>

      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        <div 
          v-for="place in places" 
          :key="place.name"
          class="group cursor-pointer"
          @click="goToPlace(place.name)"
        >
          <!-- Card -->
          <div class="aspect-square rounded-2xl overflow-hidden bg-gray-100 relative mb-3 shadow-sm group-hover:shadow-md transition-shadow">
             <img 
               :src="place.cover" 
               class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
               loading="lazy"
             />
             <div class="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors"></div>
             
             <!-- Text Overlay at Bottom Left (Google Photos style) -->
             <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/70 to-transparent text-white">
                <h3 class="font-bold text-lg truncate drop-shadow-md">{{ place.name }}</h3>
                <p class="text-xs opacity-90 drop-shadow-md">{{ place.count }} 张照片</p>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { MapPin } from 'lucide-vue-next'

const router = useRouter()
const places = ref([])
const loading = ref(true)

const fetchPlaces = async () => {
    try {
        const res = await fetch('/api/photos/places/')
        if (res.ok) {
            places.value = await res.json()
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const goToPlace = (name) => {
    // Navigate to search results for this location
    router.push({ name: 'search', query: { q: name } })
}

onMounted(fetchPlaces)
</script>
