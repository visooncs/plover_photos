<script setup>
import { onMounted, onUnmounted, ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { usePhotoStore } from '../stores/photo'
import { usePersonStore } from '../stores/person'
import { X, ArrowLeft, ArrowRight, Info, Trash2, Star, Download, Share2, ZoomIn, UserCheck, UserMinus, MapPin, RefreshCw, AlertTriangle, Camera, PlayCircle } from 'lucide-vue-next'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { wgs2gcj, addChineseTileLayer } from '../utils/mapUtils'

// Fix Leaflet icon issue
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
})

const photoStore = usePhotoStore()
const personStore = usePersonStore()
const router = useRouter()
const showInfo = ref(false)
const map = ref(null)
const videoRef = ref(null)

const currentPhoto = computed(() => photoStore.currentPhoto)

const uniqueFaces = computed(() => {
    if (!currentPhoto.value || !currentPhoto.value.faces) return []
    
    const facesMap = new Map()
    currentPhoto.value.faces.forEach(face => {
        if (face.person) {
            if (!facesMap.has(face.person)) {
                facesMap.set(face.person, {
                    ...face,
                    count: 1
                })
            } else {
                facesMap.get(face.person).count++
            }
        } else {
            // For unknown faces, we might want to deduplicate based on similarity/tracking?
            // Backend doesn't provide tracking ID yet.
            // So just treat every unknown face as unique.
            // But for video, this might be 100 unknown faces.
            // Let's skip unknown faces in the list if it's a video to avoid clutter,
            // OR just limit them.
            // For now, let's include them but using unique ID.
            facesMap.set(`unknown-${face.id}`, face)
        }
    })
    return Array.from(facesMap.values())
})
const isPlayingLivePhoto = ref(true) // Default to auto-play live photo

const playLivePhoto = () => {
    isPlayingLivePhoto.value = true
}

const handleLivePhotoEnded = () => {
    isPlayingLivePhoto.value = false
}

// Reset live photo state when photo changes
watch([currentPhoto, () => photoStore.lightboxVisible], async ([newPhoto, visible]) => {
    if (newPhoto) {
        isPlayingLivePhoto.value = true
    }
    
    // Auto-jump to timestamp if viewing a specific person in a video
    if (visible && newPhoto && (newPhoto.is_video || newPhoto.is_live_photo) && personStore.currentPerson) {
        await nextTick()
        const videoEl = videoRef.value
        if (videoEl) {
            const face = newPhoto.faces?.find(f => f.person === personStore.currentPerson.id)
            if (face && face.timestamp !== null && face.timestamp !== undefined) {
                videoEl.currentTime = Math.max(0, face.timestamp)
            }
        }
    }
})

const initMap = async () => {
    if (!currentPhoto.value || !currentPhoto.value.latitude || !currentPhoto.value.longitude) return
    if (!showInfo.value) return
    
    await nextTick()
    
    const containerId = `map-${currentPhoto.value.id}`
    const container = document.getElementById(containerId)
    
    if (!container) return
    
    // Destroy existing map if any
    if (map.value) {
        map.value.remove()
        map.value = null
    }
    
    const [lat, lng] = wgs2gcj(currentPhoto.value.latitude, currentPhoto.value.longitude)
    
    map.value = L.map(containerId).setView([lat, lng], 13)
    
    addChineseTileLayer(map.value)
    
    L.marker([lat, lng]).addTo(map.value)
}

watch([showInfo, currentPhoto], () => {
    if (showInfo.value && currentPhoto.value) {
        // Debounce map init slightly
        setTimeout(initMap, 100)
    }
})

const handleSetCover = async () => {
    if (!personStore.currentPerson || !currentPhoto.value) return
    
    // if (!confirm('确定要将这张照片设为该人物的封面吗？')) return

    try {
        await personStore.setCover(personStore.currentPerson.id, currentPhoto.value.id)
        // Simple feedback
        // In a real app, use a toast notification
        console.log('Cover updated')
    } catch (e) {
        alert('设置失败: ' + e.message)
    }
}

const handleRemoveFromPerson = async () => {
    if (!personStore.currentPerson || !currentPhoto.value) return
    
    // if (!confirm(`确定这张照片不属于 "${personStore.currentPerson.name}" 吗？`)) return

    try {
        await personStore.removePhoto(personStore.currentPerson.id, currentPhoto.value.id)
        photoStore.removePhotoFromList(currentPhoto.value.id)
        photoStore.closeLightbox()
    } catch (e) {
        alert('移除失败: ' + e.message)
    }
}

const handleRestore = async () => {
    if (!currentPhoto.value) return
    if (!confirm('确定要恢复这张照片吗？')) return
    try {
        await photoStore.restorePhoto(currentPhoto.value.id)
        photoStore.closeLightbox()
    } catch (e) {
        alert('恢复失败')
    }
}

const handlePermanentDelete = async () => {
    if (!currentPhoto.value) return
    if (!confirm('确定要永久删除这张照片吗？此操作不可恢复！')) return
    try {
        await photoStore.permanentDeletePhoto(currentPhoto.value.id)
        photoStore.closeLightbox()
    } catch (e) {
        alert('删除失败')
    }
}

const navigateToPerson = (personId) => {
    if (!personId) return
    
    // Handle case where personId might be an object
    const id = typeof personId === 'object' ? personId.id : personId
    if (!id) return

    photoStore.closeLightbox()
    
    // Use nextTick to ensure lightbox is closed before navigation (optional but safer)
    nextTick(() => {
        router.push({ name: 'person-detail', params: { id } })
    })
}

const handleDelete = async () => {
    if (!currentPhoto.value) return
    // if (!confirm('确定要删除这张照片吗？它将被移至回收站。')) return
    try {
        await photoStore.deletePhoto(currentPhoto.value.id)
        photoStore.closeLightbox()
    } catch (e) {
        alert('删除失败')
    }
}

const handleKeydown = (e) => {
    if (!photoStore.lightboxVisible) return

    switch(e.key) {
        case 'Escape':
            photoStore.closeLightbox()
            break
        case 'ArrowRight':
            photoStore.nextPhoto()
            break
        case 'ArrowLeft':
            photoStore.prevPhoto()
            break
        case 'i':
        case 'I':
            toggleInfo()
            break
    }
}

const toggleInfo = () => {
    showInfo.value = !showInfo.value
}

const formatDateTime = (dateStr) => {
    if (!dateStr) return '未知时间'
    try {
        return format(parseISO(dateStr), 'yyyy年M月d日 HH:mm', { locale: zhCN })
    } catch (e) {
        return dateStr
    }
}

const formatPersonName = (name) => {
    if (!name) return '未知'
    if (name.startsWith('人物_')) {
        return name.replace('人物_', '未命名人物 ')
    }
    return name
}

const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div v-if="photoStore.lightboxVisible" class="fixed inset-0 z-50 flex bg-black transition-opacity duration-300">
      
      <!-- Main Viewer Area -->
      <div class="flex-1 flex flex-col relative h-full min-w-0">
          
          <!-- Top Toolbar -->
          <div class="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-4 bg-gradient-to-b from-black/60 to-transparent z-20 text-white">
              <button @click="photoStore.closeLightbox" class="p-2 hover:bg-white/10 rounded-full transition-colors">
                  <ArrowLeft :size="24" />
              </button>
              
              <div class="flex items-center gap-2">
                  <button v-if="personStore.currentPerson" @click="handleRemoveFromPerson" class="p-2 hover:bg-white/10 rounded-full transition-colors" title="移出人物">
                      <UserMinus :size="20" />
                  </button>
                  
                  <template v-if="photoStore.isTrashMode">
                    <button @click="handleRestore" class="p-2 hover:bg-white/10 rounded-full transition-colors" title="恢复">
                        <RefreshCw :size="20" />
                    </button>
                    <button @click="handlePermanentDelete" class="p-2 hover:bg-red-500/50 rounded-full transition-colors text-red-400 hover:text-white" title="永久删除">
                        <AlertTriangle :size="20" />
                    </button>
                  </template>
                  <template v-else>
                    <button class="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <Star :size="20" />
                    </button>
                    <button @click="handleDelete" class="p-2 hover:bg-white/10 rounded-full transition-colors" title="删除">
                        <Trash2 :size="20" />
                    </button>
                  </template>

                  <button class="p-2 hover:bg-white/10 rounded-full transition-colors">
                      <Download :size="20" />
                  </button>
                  
                  <!-- Play Live Photo Button -->
                  <button 
                    v-if="currentPhoto && currentPhoto.is_live_photo" 
                    @click="playLivePhoto" 
                    class="p-2 hover:bg-white/10 rounded-full transition-colors" 
                    title="播放实况"
                    :class="{ 'text-blue-400': isPlayingLivePhoto }"
                  >
                      <PlayCircle :size="20" />
                  </button>

                  <button @click="toggleInfo" :class="['p-2 rounded-full transition-colors', showInfo ? 'bg-blue-500 text-white' : 'hover:bg-white/10']">
                      <Info :size="20" />
                  </button>
              </div>
          </div>

          <!-- Image Area -->
          <div class="flex-1 flex items-center justify-center relative overflow-hidden bg-black" @click.self="photoStore.closeLightbox">
              
              <!-- Nav Buttons -->
              <button 
                class="absolute left-4 p-4 rounded-full bg-black/20 hover:bg-black/40 text-white transition-colors z-10 hidden md:block"
                @click.stop="photoStore.prevPhoto"
                :disabled="photoStore.currentPhotoIndex === 0"
                :class="{ 'opacity-30 cursor-not-allowed': photoStore.currentPhotoIndex === 0 }"
              >
                  <ArrowLeft :size="32" />
              </button>

              <button 
                class="absolute right-4 p-4 rounded-full bg-black/20 hover:bg-black/40 text-white transition-colors z-10 hidden md:block"
                @click.stop="photoStore.nextPhoto"
                :disabled="photoStore.currentPhotoIndex === photoStore.photos.length - 1"
                :class="{ 'opacity-30 cursor-not-allowed': photoStore.currentPhotoIndex === photoStore.photos.length - 1 }"
              >
                  <ArrowRight :size="32" />
              </button>

              <!-- Location Badge (Bottom Right) -->
              <div v-if="currentPhoto && (currentPhoto.location_name || (currentPhoto.latitude && currentPhoto.longitude)) && !showInfo" 
                   class="absolute bottom-4 right-4 z-20 max-w-xs">
                  <button @click="toggleInfo" class="bg-black/50 hover:bg-black/70 backdrop-blur-md text-white px-4 py-2 rounded-full flex items-center gap-2 transition-all shadow-lg border border-white/10">
                      <MapPin :size="16" class="text-red-400" />
                      <span class="text-sm font-medium truncate">{{ currentPhoto.location_name || '查看位置' }}</span>
                  </button>
              </div>

              <!-- The Image / Video -->
              <div v-if="currentPhoto" class="w-full h-full flex items-center justify-center p-4">
                  <!-- Video / Live Photo Player -->
                   <!-- 
                    Logic for Live Photos vs Pure Videos:
                    - Pure Video (is_pure_video): Should behave like a normal video player (controls, autoplay usually).
                    - Live Photo (is_live_photo): 
                        - Should autoplay once? Or loop? 
                        - User request: "live photo播放一次后，就定格在照片上，除非我点击重播不然都不要在视频播放界面了"
                        - So: Autoplay once -> End -> Show Image (or Poster) -> User can click to play again.
                        - Actually, for Live Photo, usually we show the image, and maybe a "Live" badge. 
                        - When user activates it (or auto-plays once), it plays video.
                        - User says: "After playing once, freeze on photo, unless I click replay, don't show video interface".
                        - So: 
                            1. Start: Play video (autoplay)
                            2. End: Switch to Image view (hide video element, show img element).
                            3. Interaction: Allow user to trigger video playback again.
                   -->

                  <template v-if="currentPhoto.is_live_photo">
                     <div class="relative w-full h-full flex items-center justify-center">
                        <video 
                            v-if="isPlayingLivePhoto"
                            ref="videoRef"
                            :src="currentPhoto.video_url"
                            autoplay
                            class="max-w-full max-h-full shadow-2xl"
                            @ended="handleLivePhotoEnded"
                        ></video>
                        <img 
                            v-else
                            :src="currentPhoto.url + '?size=1600'" 
                            class="max-w-full max-h-full object-contain shadow-2xl cursor-pointer" 
                            :alt="currentPhoto.location_name"
                        />
                     </div>
                  </template>

                  <video 
                    v-else-if="currentPhoto.is_video"
                    ref="videoRef"
                    :src="currentPhoto.video_url"
                    controls
                    autoplay
                    class="max-w-full max-h-full shadow-2xl"
                  ></video>
                  
                  <!-- Normal Image -->
                  <img 
                    v-else
                    :src="currentPhoto.url + '?size=1600'" 
                    class="max-w-full max-h-full object-contain shadow-2xl" 
                    :alt="currentPhoto.location_name" 
                  />
              </div>
          </div>
      </div>

      <!-- Info Sidebar -->
      <div v-if="showInfo" class="w-80 bg-white border-l border-gray-200 flex flex-col h-full overflow-y-auto transition-all duration-300 z-20">
          <div class="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 class="font-medium text-lg text-gray-800">详细信息</h3>
              <button @click="toggleInfo" class="p-1 hover:bg-gray-100 rounded-full text-gray-500">
                  <X :size="20" />
              </button>
          </div>
          
          <div v-if="currentPhoto" class="p-6 space-y-6">
              <!-- Person Actions -->
              <div v-if="personStore.currentPerson" class="flex items-center justify-between bg-blue-50 p-3 rounded-lg">
                  <span class="text-sm text-blue-800">当前人物: {{ personStore.currentPerson.name }}</span>
                  <button 
                    @click="handleSetCover"
                    class="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-full transition-colors"
                    title="设为封面"
                  >
                      <UserCheck :size="14" />
                      <span>设为封面</span>
                  </button>
              </div>

              <!-- Identified People List -->
              <div v-if="currentPhoto.faces && currentPhoto.faces.length > 0">
                  <div class="flex items-start gap-3">
                      <div class="mt-1 text-gray-400"><UserCheck :size="20" /></div>
                      <div>
                            <div class="text-sm text-gray-500">识别出的人物</div>
                            <div class="flex flex-wrap gap-2 mt-1">
                                <span 
                                    v-for="face in uniqueFaces" 
                                    :key="face.id"
                                    @click="navigateToPerson(face.person)"
                                    class="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                                    :class="{'cursor-default': !face.person, 'cursor-pointer hover:text-blue-600': face.person}"
                                >
                                    {{ formatPersonName(face.person_name) }} 
                                    <span v-if="face.count > 1" class="ml-1 px-1 bg-gray-200 rounded-full text-[10px]">{{ face.count }}</span>
                                    <span v-else>({{ Math.round(face.prob * 100) }}%)</span>
                                </span>
                            </div>
                        </div>
                  </div>
              </div>

              <!-- Description -->
              <div v-if="currentPhoto.description">
                  <p class="text-gray-700">{{ currentPhoto.description }}</p>
              </div>

              <!-- Date -->
              <div class="flex items-start gap-3">
                  <div class="mt-1 text-gray-400"><Info :size="20" /></div>
                  <div>
                      <div class="text-sm text-gray-500">拍摄时间</div>
                      <div class="text-gray-800">{{ formatDateTime(currentPhoto.captured_at) }}</div>
                  </div>
              </div>

              <!-- File Name -->
              <div class="flex items-start gap-3">
                  <div class="mt-1 text-gray-400"><Share2 :size="20" /></div>
                  <div>
                      <div class="text-sm text-gray-500">文件名</div>
                      <div class="text-gray-800 break-all">{{ currentPhoto.file_path ? currentPhoto.file_path.split(/[\\/]/).pop() : 'Unknown' }}</div>
                  </div>
              </div>

              <!-- Resolution & Size -->
              <div class="flex items-start gap-3">
                  <div class="mt-1 text-gray-400"><ZoomIn :size="20" /></div>
                  <div>
                      <div class="text-sm text-gray-500">分辨率与大小</div>
                      <div class="text-gray-800">{{ currentPhoto.width }} x {{ currentPhoto.height }}</div>
                      <div class="text-gray-600 text-sm">{{ formatFileSize(currentPhoto.size) }}</div>
                  </div>
              </div>

              <!-- EXIF Info -->
              <div v-if="currentPhoto.exif_camera_model || currentPhoto.exif_iso" class="flex items-start gap-3">
                  <div class="mt-1 text-gray-400"><Camera :size="20" /></div>
                  <div>
                      <div class="text-sm text-gray-500">相机参数</div>
                      <div v-if="currentPhoto.exif_camera_model" class="text-gray-800 font-medium">
                          {{ currentPhoto.exif_camera_model }}
                      </div>
                      <div v-if="currentPhoto.exif_lens_model" class="text-xs text-gray-500 mb-1">
                          {{ currentPhoto.exif_lens_model }}
                      </div>
                      <div class="flex flex-wrap gap-2 text-xs text-gray-600 bg-gray-50 p-2 rounded mt-1">
                          <span v-if="currentPhoto.exif_f_number">f/{{ currentPhoto.exif_f_number }}</span>
                          <span v-if="currentPhoto.exif_exposure_time">{{ currentPhoto.exif_exposure_time }}s</span>
                          <span v-if="currentPhoto.exif_iso">ISO{{ currentPhoto.exif_iso }}</span>
                          <span v-if="currentPhoto.exif_focal_length">{{ currentPhoto.exif_focal_length }}mm</span>
                      </div>
                  </div>
              </div>

              <!-- Location Map -->
              <div v-if="currentPhoto.latitude && currentPhoto.longitude" class="mt-4">
                  <div class="flex items-start gap-3 mb-2">
                      <div class="mt-1 text-gray-400"><MapPin :size="20" /></div>
                      <div>
                          <div class="text-sm text-gray-500">位置</div>
                          <div class="text-gray-800">{{ currentPhoto.location_name || `${currentPhoto.latitude?.toFixed(4)}, ${currentPhoto.longitude?.toFixed(4)}` }}</div>
                      </div>
                  </div>
                  
                  <div class="h-48 rounded-xl overflow-hidden bg-gray-100 border border-gray-200 relative z-0">
                      <div :id="`map-${currentPhoto.id}`" class="w-full h-full"></div>
                  </div>
              </div>
          </div>
      </div>

  </div>
</template>

<style scoped>
/* Custom Scrollbar for Info Sidebar */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 3px;
}
/* Leaflet z-index fix */
:deep(.leaflet-pane) {
    z-index: 10 !important;
}
:deep(.leaflet-control) {
    z-index: 11 !important;
}
</style>
