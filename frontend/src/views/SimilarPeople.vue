<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePersonStore } from '../stores/person'
import { ArrowLeft, CheckCircle, Circle, Merge, AlertTriangle, User } from 'lucide-vue-next'
import { useWindowSize } from '@vueuse/core'

const route = useRoute()
const router = useRouter()
const personStore = usePersonStore()

const targetPersonId = route.params.id
const threshold = ref(0.4) // Default stricter threshold
const similarPeople = ref([])
const loading = ref(false)
const selectedPersonIds = ref(new Set())
const processing = ref(false)

const { width } = useWindowSize()

const currentCols = computed(() => {
  if (width.value >= 1280) return 8
  if (width.value >= 1024) return 6
  if (width.value >= 768) return 5
  if (width.value >= 640) return 4
  return 3
})

const fetchSimilar = async () => {
    loading.value = true
    try {
        const res = await fetch(`/api/people/${targetPersonId}/similar/?threshold=${threshold.value}`)
        if (!res.ok) throw new Error('Failed to fetch similar people')
        similarPeople.value = await res.json()
        // Reset selection when results change
        selectedPersonIds.value.clear()
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

// Fetch when mounted or threshold changes (debounced)
let debounceTimer = null
watch(threshold, () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
        fetchSimilar()
    }, 500)
})

onMounted(async () => {
    await personStore.fetchPerson(targetPersonId)
    fetchSimilar()
})

const toggleSelection = (id) => {
    if (selectedPersonIds.value.has(id)) {
        selectedPersonIds.value.delete(id)
    } else {
        selectedPersonIds.value.add(id)
    }
}

const handleMerge = async () => {
    if (selectedPersonIds.value.size === 0) return
    // if (!confirm(`确定将选中的 ${selectedPersonIds.value.size} 个人物合并到当前人物吗？此操作不可撤销。`)) return

    processing.value = true
    try {
        const response = await fetch(`/api/people/${targetPersonId}/merge/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ source_ids: Array.from(selectedPersonIds.value) }),
        })
        
        if (!response.ok) throw new Error('Merge failed')
        
        // Refresh
        await fetchSimilar()
    } catch (e) {
        alert('合并失败: ' + e.message)
    } finally {
        processing.value = false
    }
}

const selectAll = () => {
    if (selectedPersonIds.value.size === similarPeople.value.length) {
        selectedPersonIds.value.clear()
    } else {
        similarPeople.value.forEach(p => selectedPersonIds.value.add(p.id))
    }
}

</script>

<template>
  <div class="min-h-full bg-white">
      <!-- Header -->
      <div class="pt-6 px-4 sm:px-8 pb-4 border-b border-gray-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sticky top-0 bg-white/95 backdrop-blur z-20">
          <div class="flex items-center gap-4">
              <router-link :to="{ name: 'person-detail', params: { id: targetPersonId } }" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
                  <ArrowLeft :size="24" class="text-gray-600" />
              </router-link>
              <div>
                  <h1 class="text-xl font-bold text-gray-900 flex items-center gap-2">
                      合并相似人物
                      <span v-if="personStore.currentPerson" class="text-gray-500 font-normal text-base">
                          (目标: {{ personStore.currentPerson.name }})
                      </span>
                  </h1>
                  <p class="text-sm text-gray-500 mt-1">调整相似度阈值以查找更多或更精确的结果</p>
              </div>
          </div>

          <div class="flex items-center gap-4 w-full sm:w-auto">
               <div class="flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-lg flex-1 sm:flex-none">
                  <span class="text-xs font-medium text-gray-500 whitespace-nowrap">相似度: {{ threshold }}</span>
                  <input 
                    type="range" 
                    min="0.1" 
                    max="0.8" 
                    step="0.05" 
                    v-model.number="threshold" 
                    class="w-32 accent-blue-600 cursor-pointer"
                  >
               </div>

               <button 
                  @click="handleMerge"
                  :disabled="selectedPersonIds.size === 0 || processing"
                  class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                   <Merge :size="18" />
                   <span class="font-medium">合并 {{ selectedPersonIds.size > 0 ? `(${selectedPersonIds.size})` : '' }}</span>
               </button>
          </div>
      </div>

      <!-- Content -->
      <div class="p-4 sm:p-8">
          <div v-if="loading" class="flex justify-center py-12">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
          
          <div v-else-if="similarPeople.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-500">
              <div class="bg-gray-100 p-4 rounded-full mb-4">
                  <CheckCircle :size="32" class="text-gray-400" />
              </div>
              <p>未找到相似人物</p>
              <p class="text-sm mt-2">尝试调高相似度阈值 (向右拖动滑块)</p>
          </div>

          <div v-else>
              <div class="mb-4 flex items-center justify-between">
                  <span class="text-sm text-gray-500">找到 {{ similarPeople.length }} 个相似人物</span>
                  <button @click="selectAll" class="text-sm text-blue-600 hover:text-blue-700 font-medium">
                      {{ selectedPersonIds.size === similarPeople.length ? '取消全选' : '全选' }}
                  </button>
              </div>

              <div class="grid gap-4" :style="{ gridTemplateColumns: `repeat(${currentCols}, minmax(0, 1fr))` }">
                  <div 
                    v-for="person in similarPeople" 
                    :key="person.id"
                    class="group relative aspect-square bg-gray-100 rounded-xl overflow-hidden cursor-pointer border-2 transition-all duration-200"
                    :class="selectedPersonIds.has(person.id) ? 'border-blue-500 ring-2 ring-blue-200' : 'border-transparent hover:border-gray-300'"
                    @click="toggleSelection(person.id)"
                  >
                      <img 
                        v-if="person.face_url" 
                        :src="person.face_url" 
                        class="w-full h-full object-cover"
                        loading="lazy"
                      />
                      <div v-else class="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400">
                          <User :size="32" />
                      </div>

                      <!-- Selection Indicator -->
                      <div class="absolute top-2 right-2 z-10">
                         <div class="bg-white rounded-full p-0.5 shadow-sm">
                             <CheckCircle v-if="selectedPersonIds.has(person.id)" class="text-blue-600 fill-white" :size="24" />
                             <Circle v-else class="text-gray-300 bg-white/50 rounded-full" :size="24" />
                         </div>
                      </div>

                      <!-- Info Overlay -->
                      <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 pt-8">
                          <p class="text-white font-medium text-sm truncate">{{ person.name }}</p>
                          <div class="flex items-center justify-between mt-1">
                              <span class="text-xs text-gray-300">{{ person.photo_count }} 张照片</span>
                              <span 
                                class="text-[10px] font-bold px-1.5 py-0.5 rounded text-white"
                                :class="person.distance < 0.3 ? 'bg-green-500/80' : (person.distance < 0.5 ? 'bg-yellow-500/80' : 'bg-red-500/80')"
                              >
                                  Sim: {{ (1 - person.distance).toFixed(2) }}
                              </span>
                          </div>
                      </div>
                  </div>
              </div>
          </div>
      </div>
  </div>
</template>
