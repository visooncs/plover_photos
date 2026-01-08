<script setup>
import { onMounted, onUnmounted, watch, ref, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { usePersonStore } from '../stores/person'
import { usePhotoStore } from '../stores/photo'
import PhotoGrid from '../components/PhotoGrid.vue'
import PhotoLightbox from '../components/PhotoLightbox.vue'
import { ArrowLeft, Edit2, ScanSearch } from 'lucide-vue-next'

const route = useRoute()
const personStore = usePersonStore()
const photoStore = usePhotoStore()

const isEditing = ref(false)
const editedName = ref('')
const nameInput = ref(null)

const startEditing = () => {
    if (personStore.currentPerson) {
        editedName.value = personStore.currentPerson.name
        isEditing.value = true
        nextTick(() => {
            nameInput.value?.focus()
        })
    }
}

const saveName = async () => {
    if (!editedName.value.trim()) {
        isEditing.value = false
        return
    }
    
    if (editedName.value === personStore.currentPerson.name) {
        isEditing.value = false
        return
    }

    try {
        await personStore.updatePersonName(personStore.currentPerson.id, editedName.value)
    } catch (e) {
        console.error(e)
    } finally {
        isEditing.value = false
    }
}

const loadData = async () => {
    const personId = route.params.id
    if (personId) {
        // Fetch Person Details
        await personStore.fetchPerson(personId)
        
        // Fetch Person Photos
        photoStore.clearPhotos()
        await photoStore.fetchPhotos('/api/photos/', { people: personId })
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
    personStore.clearCurrentPerson()
})
</script>

<template>
  <div class="min-h-full bg-white">
    <!-- Header -->
    <div class="pt-6 px-4 sm:px-8 pb-4 border-b border-gray-100 flex items-center gap-4">
        <router-link to="/people" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <ArrowLeft :size="24" class="text-gray-600" />
        </router-link>
        
        <div v-if="personStore.error" class="text-red-500">
            加载失败: {{ personStore.error }}
        </div>
        <div v-else-if="personStore.currentPerson" class="flex items-center gap-4">
             <div class="w-16 h-16 rounded-full overflow-hidden border-2 border-white shadow-sm">
                <img 
                    v-if="personStore.currentPerson.face_url || personStore.currentPerson.avatar" 
                    :src="personStore.currentPerson.face_url || personStore.currentPerson.avatar.thumbnail" 
                    class="w-full h-full object-cover"
                    :style="personStore.currentPerson.face_url ? '' : 'object-position: center 20%;'"
                />
                <div v-else class="w-full h-full bg-gray-200"></div>
            </div>
            <div>
                <div v-if="!isEditing" class="group flex items-center gap-2 cursor-pointer" @click="startEditing">
                    <h1 class="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{{ personStore.currentPerson.name }}</h1>
                    <Edit2 :size="16" class="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                 <div v-else>
                    <input 
                        ref="nameInput"
                        v-model="editedName" 
                        @blur="saveName" 
                        @keyup.enter="saveName"
                        class="text-2xl font-bold text-gray-900 border-b-2 border-blue-500 outline-none"
                    />
                </div>
                <div class="text-sm text-gray-500 mt-1">
                    {{ photoStore.count }} 张照片
                </div>
            </div>
            
            <router-link 
                :to="{ name: 'person-similar', params: { id: personStore.currentPerson.id } }" 
                class="ml-auto sm:ml-4 p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors" 
                title="查找相似人物"
            >
                <ScanSearch :size="24" />
            </router-link>
        </div>
        <div v-else-if="personStore.loading" class="h-10 w-48 bg-gray-200 animate-pulse rounded"></div>
    </div>

    <!-- Photos -->
    <PhotoGrid />
    <PhotoLightbox />
  </div>
</template>
