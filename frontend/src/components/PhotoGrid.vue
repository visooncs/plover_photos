<script setup>
import { usePhotoStore } from '../stores/photo'
import { Check, Play } from 'lucide-vue-next'
import { useIntersectionObserver, useWindowSize } from '@vueuse/core'
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  isSelectionMode: {
    type: Boolean,
    default: false
  }
})

const photoStore = usePhotoStore()
const loadMoreTrigger = ref(null)

const { width } = useWindowSize()

const currentCols = computed(() => {
  if (width.value >= 1280) return 8
  if (width.value >= 1024) return 6
  if (width.value >= 768) return 5
  if (width.value >= 640) return 4
  return 3
})

const flattenedItems = computed(() => {
  const items = []
  const cols = currentCols.value
  
  photoStore.groupedPhotos.forEach(group => {
    // Header item
    items.push({
      id: `header-${group.id}`,
      type: 'header',
      title: group.title,
      count: group.photos.length
    })
    
    // Row items
    for (let i = 0; i < group.photos.length; i += cols) {
      items.push({
        id: `row-${group.id}-${i}`,
        type: 'row',
        photos: group.photos.slice(i, i + cols)
      })
    }
  })
  return items
})

const imgSizes = computed(() => {
  return `${Math.ceil(100 / currentCols.value)}vw`
})

const hoverPhotoId = ref(null)
const hoverTimeout = ref(null)
const isVideoReady = ref(false)

useIntersectionObserver(
  loadMoreTrigger,
  ([{ isIntersecting }]) => {
    if (isIntersecting && photoStore.nextUrl) {
      photoStore.loadMore()
    }
  },
)

const handleMouseEnter = (photo) => {
  if (photo.is_live_photo && photo.video_url) {
    hoverTimeout.value = setTimeout(() => {
      isVideoReady.value = false
      hoverPhotoId.value = photo.id
    }, 300) // 延迟 300ms 播放，避免快速划过时触发
  }
}

const handleMouseLeave = () => {
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value)
    hoverTimeout.value = null
  }
  hoverPhotoId.value = null
  isVideoReady.value = false
}

const handlePhotoClick = (photo, event) => {
    if (props.isSelectionMode) {
        photoStore.toggleSelection(photo.id)
    } else {
        photoStore.openLightbox(photo)
    }
}

const toggleSelection = (photo, event) => {
    event.stopPropagation()
    photoStore.toggleSelection(photo.id)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div v-if="photoStore.loading && photoStore.count === 0" class="flex justify-center items-center h-64">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <DynamicScroller
      v-else
      :items="flattenedItems"
      :min-item-size="100"
      class="flex-1"
      key-field="id"
    >
      <template v-slot="{ item, index, active }">
        <DynamicScrollerItem
          :item="item"
          :active="active"
          :size-dependencies="[item.type, currentCols]"
          :data-index="index"
        >
          <!-- Date Header -->
          <div v-if="item.type === 'header'" class="sticky top-0 bg-white/90 backdrop-blur-md z-10 pt-4 pb-2 px-2 flex items-baseline gap-2 border-b border-gray-100/50 transition-all">
            <h2 class="text-lg font-medium text-gray-800">{{ item.title }}</h2>
            <span class="text-xs text-gray-500">{{ item.count }} 张照片</span>
          </div>

          <!-- Photo Grid Row -->
          <div v-else class="grid gap-2 px-2 pb-2" :style="{ gridTemplateColumns: `repeat(${currentCols}, minmax(0, 1fr))` }">
            <div 
              v-for="photo in item.photos" 
              :key="photo.id" 
              class="group relative aspect-square bg-gray-100 cursor-pointer overflow-hidden rounded-lg transition-all duration-200"
              @click="handlePhotoClick(photo)"
              @mouseenter="handleMouseEnter(photo)"
              @mouseleave="handleMouseLeave"
            >
              <!-- Image -->
              <img 
                :src="photo.thumbnail" 
                :srcset="`${photo.url}?size=150&crop=1 150w, ${photo.url}?size=300&crop=1 300w, ${photo.url}?size=600&crop=1 600w`"
                :sizes="imgSizes"
                :alt="photo.location_name || 'Photo'" 
                loading="lazy" 
                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              
              <!-- Live Photo Preview -->
              <video 
                v-if="hoverPhotoId === photo.id"
                :src="photo.video_url"
                autoplay
                muted
                loop
                playsinline
                class="absolute inset-0 w-full h-full object-cover transition-opacity duration-300"
                :class="[isVideoReady ? 'opacity-100' : 'opacity-0']"
                @canplay="isVideoReady = true"
              ></video>

              <!-- Hover Overlay -->
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-200"></div>

              <!-- Selection Checkbox -->
              <div 
                v-if="isSelectionMode || photoStore.selectedPhotoIds.has(photo.id)"
                class="absolute top-2 left-2 z-20 transition-opacity duration-200"
                :class="[isSelectionMode || photoStore.selectedPhotoIds.has(photo.id) ? 'opacity-100' : 'opacity-0 group-hover:opacity-100']"
                @click="(e) => toggleSelection(photo, e)"
              >
                  <div 
                    class="w-6 h-6 rounded-full border-2 transition-colors flex items-center justify-center shadow-sm"
                    :class="[
                        photoStore.selectedPhotoIds.has(photo.id) 
                            ? 'bg-blue-600 border-blue-600' 
                            : 'border-white/70 bg-black/20 hover:bg-black/40'
                    ]"
                  >
                      <Check v-if="photoStore.selectedPhotoIds.has(photo.id)" :size="14" class="text-white" />
                  </div>
              </div>

              <!-- Selection Overlay (when selected) -->
              <div v-if="photoStore.selectedPhotoIds.has(photo.id)" class="absolute inset-0 bg-blue-600/20 border-4 border-blue-600 rounded-lg z-10 pointer-events-none"></div>
              
              <!-- Video/Live Indicator -->
              <div class="absolute top-2 right-2 text-white z-20">
                   <div v-if="photo.is_live_photo" class="flex items-center gap-1.5 bg-black/50 backdrop-blur-sm rounded-full px-2 py-1 border border-white/20 shadow-sm">
                       <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="text-white drop-shadow-sm">
                           <circle cx="12" cy="12" r="10" stroke-dasharray="4 4" class="opacity-80"></circle>
                           <circle cx="12" cy="12" r="5" fill="currentColor"></circle>
                       </svg>
                       <span class="text-[10px] font-bold tracking-wider text-white">LIVE</span>
                   </div>
                   <div v-else-if="photo.is_video" class="drop-shadow-md">
                        <Play :size="16" class="fill-current" />
                   </div>
              </div>
            </div>
          </div>
        </DynamicScrollerItem>
      </template>
      
      <template #after>
        <!-- Load More Trigger -->
        <div ref="loadMoreTrigger" class="flex justify-center py-8 h-20">
            <div v-if="photoStore.loading && photoStore.photos.length > 0" class="flex gap-2 items-center text-gray-400">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
                <span class="text-sm">加载更多...</span>
            </div>
        </div>
      </template>
    </DynamicScroller>
  </div>
</template>

<style scoped>
</style>
