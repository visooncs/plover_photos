<script setup>
import { onMounted, ref, computed, nextTick } from 'vue'
import { usePersonStore } from '../stores/person'
import { useRouter } from 'vue-router'
import { User, CheckCircle, Circle, Merge, Eye, EyeOff, Star, Pencil } from 'lucide-vue-next'
import { useIntersectionObserver, useWindowSize } from '@vueuse/core'

const personStore = usePersonStore()
const router = useRouter()
const loadMoreTrigger = ref(null)
const showHidden = ref(false)

const { width } = useWindowSize()

const currentCols = computed(() => {
  if (width.value >= 1280) return 8
  if (width.value >= 1024) return 6
  if (width.value >= 768) return 5
  if (width.value >= 640) return 4
  return 3
})

const flattenedPeople = computed(() => {
  const items = []
  const cols = currentCols.value
  for (let i = 0; i < personStore.people.length; i += cols) {
    items.push({
      id: `row-${i}`,
      people: personStore.people.slice(i, i + cols)
    })
  }
  return items
})

const imgSizes = computed(() => {
  return `${Math.ceil(100 / currentCols.value)}vw`
})

const isSelectionMode = ref(false)
const selectedPersonIds = ref(new Set())
const showMergeDialog = ref(false)
const targetPersonId = ref(null)

// Inline editing state
const editingId = ref(null)
const editingName = ref('')
const nameInput = ref(null)

const selectedPeople = computed(() => {
  return personStore.people.filter(p => selectedPersonIds.value.has(p.id))
})

useIntersectionObserver(
  loadMoreTrigger,
  ([{ isIntersecting }]) => {
    if (isIntersecting && personStore.nextUrl) {
      personStore.loadMore()
    }
  },
)

onMounted(() => {
  if (personStore.people.length === 0) {
    personStore.fetchPeople()
  }
})

const openPerson = (id) => {
  router.push({ name: 'person-detail', params: { id } })
}

const toggleSelectionMode = () => {
  isSelectionMode.value = !isSelectionMode.value
  selectedPersonIds.value.clear()
}

const toggleSelection = (id) => {
  if (selectedPersonIds.value.has(id)) {
    selectedPersonIds.value.delete(id)
  } else {
    selectedPersonIds.value.add(id)
  }
}

const handlePersonClick = (id) => {
  if (isSelectionMode.value) {
    toggleSelection(id)
  } else if (editingId.value !== id) {
    openPerson(id)
  }
}

const startEdit = (person, e) => {
    e.stopPropagation()
    editingId.value = person.id
    editingName.value = person.name
    nextTick(() => {
        const input = document.querySelector(`.name-input-${person.id}`)
        if (input) input.focus()
    })
}

const handleSaveName = async (person) => {
    if (!editingName.value.trim() || editingName.value === person.name) {
        editingId.value = null
        return
    }

    try {
        await personStore.updatePersonName(person.id, editingName.value.trim())
        editingId.value = null
    } catch (e) {
        alert('修改名称失败: ' + e.message)
    }
}

const handleCancelEdit = () => {
    editingId.value = null
}

const toggleShowHidden = () => {
  showHidden.value = !showHidden.value
  personStore.people = []
  personStore.fetchPeople(`/api/people/?show_hidden=${showHidden.value}`)
}

const handleHide = async (person, e) => {
    e.stopPropagation()
    const action = showHidden.value ? 'unhide' : 'hide'
    
    if (showHidden.value) {
        // if (!confirm(`确定要恢复显示人物 "${person.name}" 吗？`)) return
    }

    // Optimistic update
    const index = personStore.people.findIndex(p => p.id === person.id)
    if (index !== -1) {
        personStore.people.splice(index, 1)
    }
    
    try {
        await fetch(`/api/people/${person.id}/${action}/`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
    } catch (e) {
        console.error(e)
    }
}

const handleStar = async (person, e) => {
    e.stopPropagation()
    const newStatus = !person.is_starred
    // Optimistic update
    person.is_starred = newStatus
    
    const action = newStatus ? 'star' : 'unstar'
    try {
        await fetch(`/api/people/${person.id}/${action}/`, {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' }
        })
    } catch (e) {
        console.error(e)
        person.is_starred = !newStatus // revert
    }
}

const openMergeDialog = () => {
    if (selectedPersonIds.value.size < 2) return
    // Default target to the first selected person (usually the one with most photos due to sort)
    // Actually we should let user choose, but pre-select the "best" one
    const sortedSelected = [...selectedPeople.value].sort((a, b) => b.photo_count - a.photo_count)
    targetPersonId.value = sortedSelected[0].id
    showMergeDialog.value = true
}

const confirmMerge = async () => {
    if (!targetPersonId.value) return
    
    const sourceIds = Array.from(selectedPersonIds.value).filter(id => id !== targetPersonId.value)
    
    try {
        const response = await fetch(`/api/people/${targetPersonId.value}/merge/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_ids: sourceIds })
        })
        
        if (response.ok) {
             // Reset
            selectedPersonIds.value.clear()
            isSelectionMode.value = false
            showMergeDialog.value = false
            // Reload
            personStore.people = []
            personStore.fetchPeople()
        }
    } catch (e) {
        console.error(e)
    }
}
</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <div class="p-6 border-b border-gray-100 flex justify-between items-center flex-shrink-0">
        <h1 class="text-2xl font-bold text-gray-900">人物</h1>
        <div class="flex gap-2">
            <button 
                v-if="isSelectionMode && selectedPersonIds.size >= 2"
                @click="openMergeDialog"
                class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
                <Merge :size="16" />
                合并 ({{ selectedPersonIds.size }})
            </button>
            <button 
                @click="toggleSelectionMode"
                class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                :class="isSelectionMode ? 'bg-gray-200 text-gray-800' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'"
            >
                {{ isSelectionMode ? '取消选择' : '选择' }}
            </button>
            <button 
                @click="toggleShowHidden"
                class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                :class="showHidden ? 'bg-gray-800 text-white' : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'"
            >
                {{ showHidden ? '返回列表' : '已隐藏' }}
            </button>
        </div>
    </div>
    
    <div v-if="personStore.loading && personStore.people.length === 0" class="flex justify-center h-64 items-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <DynamicScroller
      v-else
      :items="flattenedPeople"
      :min-item-size="150"
      class="flex-1 p-6"
      key-field="id"
    >
      <template v-slot="{ item, index, active }">
        <DynamicScrollerItem
          :item="item"
          :active="active"
          :size-dependencies="[currentCols]"
          :data-index="index"
        >
          <div class="grid gap-6 mb-8" :style="{ gridTemplateColumns: `repeat(${currentCols}, minmax(0, 1fr))` }">
            <div 
              v-for="person in item.people" 
              :key="person.id"
              class="group cursor-pointer flex flex-col items-center relative"
              @click="handlePersonClick(person.id)"
            >
              <!-- Avatar Container with selection checkmark -->
              <div class="relative w-full aspect-square mb-3">
                <div class="w-full h-full rounded-full overflow-hidden bg-gray-100 shadow-sm group-hover:shadow-md transition-shadow relative">
                  <img 
                    v-if="person.face_url || person.avatar" 
                    :src="person.face_url || person.avatar.thumbnail" 
                    :srcset="person.face_url ? `${person.face_url}?size=100 100w, ${person.face_url}?size=200 200w, ${person.face_url}?size=400 400w` : ''"
                    :sizes="imgSizes"
                    :alt="person.name"
                    class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    :style="person.face_url ? '' : 'object-position: center 20%;'"
                    loading="lazy"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center bg-gray-200">
                    <User :size="32" class="text-gray-400" />
                  </div>
                  
                  <!-- Selection Overlay (Dimming) -->
                  <div v-if="isSelectionMode" class="absolute inset-0 bg-black/10 transition-opacity"></div>
                </div>

                <!-- Hide Button (Moved outside overflow-hidden) -->
                <button 
                    v-if="!isSelectionMode"
                    @click="(e) => handleHide(person, e)"
                    class="absolute top-1 right-1 z-20 p-1.5 rounded-full bg-white/80 hover:bg-white text-gray-600 hover:text-gray-900 opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                    :title="showHidden ? '恢复显示' : '隐藏人物'"
                >
                    <Eye v-if="showHidden" :size="16" />
                    <EyeOff v-else :size="16" />
                </button>

                <!-- Star Button -->
                <button 
                    v-if="!isSelectionMode"
                    @click="(e) => handleStar(person, e)"
                    class="absolute top-1 left-1 z-20 p-1.5 rounded-full transition-all shadow-sm"
                    :class="person.is_starred ? 'bg-white text-yellow-500 opacity-100' : 'bg-white/80 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-yellow-500'"
                    :title="person.is_starred ? '取消标星' : '标星人物'"
                >
                    <Star :size="16" :fill="person.is_starred ? 'currentColor' : 'none'" />
                </button>

                <!-- Selection Checkmark (Outside overflow-hidden to avoid clipping) -->
                <div v-if="isSelectionMode" class="absolute top-1 right-1 z-10">
                   <div class="bg-white rounded-full p-0.5 shadow-sm">
                       <CheckCircle v-if="selectedPersonIds.has(person.id)" class="text-blue-600 fill-white" :size="26" />
                       <Circle v-else class="text-gray-300" :size="26" />
                   </div>
                </div>
              </div>
              
              <h3 class="font-medium text-gray-900 truncate text-center w-full group/name relative flex items-center justify-center gap-1 min-h-[24px]">
                <template v-if="editingId === person.id">
                  <input 
                    v-model="editingName"
                    :class="`name-input-${person.id}`"
                    class="w-full text-center border-b-2 border-blue-500 focus:outline-none bg-transparent py-0.5"
                    @blur="handleSaveName(person)"
                    @keyup.enter="handleSaveName(person)"
                    @keyup.esc="handleCancelEdit"
                    @click.stop
                  />
                </template>
                <template v-else>
                  <span class="truncate">{{ person.name }}</span>
                  <button 
                    v-if="!isSelectionMode"
                    @click="(e) => startEdit(person, e)"
                    class="opacity-0 group-hover/name:opacity-100 p-1 hover:text-blue-600 transition-opacity"
                    title="重命名"
                  >
                    <Pencil :size="14" />
                  </button>
                </template>
              </h3>
              <p class="text-xs text-gray-500">{{ person.photo_count }} 张照片</p>
            </div>
          </div>
        </DynamicScrollerItem>
      </template>

      <template #after>
        <!-- Infinite Scroll Sentinel -->
        <div ref="loadMoreTrigger" class="h-20 flex justify-center items-center mt-8">
          <div v-if="personStore.loading && personStore.people.length > 0" class="flex gap-2 items-center text-gray-400">
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
            <span class="text-sm">加载更多...</span>
          </div>
        </div>
      </template>
    </DynamicScroller>
    
    <!-- Merge Dialog -->
    <div v-if="showMergeDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 class="text-xl font-bold mb-4">合并人物</h2>
            <p class="text-gray-600 mb-4">选择保留的人物名称 (其他人物将被合并到此人物):</p>
            
            <div class="space-y-2 max-h-60 overflow-y-auto mb-6">
                <div 
                    v-for="person in selectedPeople" 
                    :key="person.id"
                    @click="targetPersonId = person.id"
                    class="flex items-center gap-3 p-3 rounded-lg cursor-pointer border-2 transition-all"
                    :class="targetPersonId === person.id ? 'border-blue-500 bg-blue-50' : 'border-transparent hover:bg-gray-50'"
                >
                    <div class="w-10 h-10 rounded-full overflow-hidden bg-gray-200 flex-shrink-0">
                         <img 
                            v-if="person.face_url || person.avatar" 
                            :src="person.face_url || person.avatar.thumbnail" 
                            class="w-full h-full object-cover"
                        />
                    </div>
                    <div class="flex-1">
                        <div class="font-medium">{{ person.name }}</div>
                        <div class="text-xs text-gray-500">{{ person.photo_count }} 张照片</div>
                    </div>
                    <div v-if="targetPersonId === person.id" class="text-blue-600">
                        <CheckCircle :size="20" />
                    </div>
                </div>
            </div>
            
            <div class="flex justify-end gap-3">
                <button 
                    @click="showMergeDialog = false"
                    class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                    取消
                </button>
                <button 
                    @click="confirmMerge"
                    class="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg"
                >
                    确认合并
                </button>
            </div>
        </div>
    </div>
  </div>
</template>
