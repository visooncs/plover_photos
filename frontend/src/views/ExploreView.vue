<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Image, Sparkles, MapPin, Calendar, User, Clock, ArrowRight } from 'lucide-vue-next'
import axios from 'axios'

const router = useRouter()

const recommendations = ref([])
const loadingRecs = ref(false)
const memories = ref([])
const loadingMemories = ref(false)

onMounted(() => {
  fetchMemories()
  fetchRecommendations()
})

const fetchMemories = async () => {
    loadingMemories.value = true
    try {
        const res = await axios.get('/api/memories/')
        memories.value = res.data.results || res.data
        
        // 如果没有回忆，尝试触发生成
        if (memories.value.length === 0) {
             await axios.post('/api/memories/generate/')
             const retryRes = await axios.get('/api/memories/')
             memories.value = retryRes.data.results || retryRes.data
        }
    } catch (e) {
        console.error("Failed to fetch memories", e)
    } finally {
        loadingMemories.value = false
    }
}

const fetchRecommendations = async () => {
    loadingRecs.value = true
    try {
        const res = await axios.get('/api/albums/recommendations/')
        recommendations.value = res.data
    } catch (e) {
        console.error("Failed to fetch recommendations", e)
    } finally {
        loadingRecs.value = false
    }
}

const saveRecommendation = async (rec) => {
    // if (!confirm(`确定要将 "${rec.title}" 保存为相册吗？`)) return
    
    try {
        const res = await axios.post('/api/albums/save_recommendation/', rec)
        // Remove from recommendations locally
        recommendations.value = recommendations.value.filter(r => r.id !== rec.id)
        
        router.push({ name: 'album-detail', params: { id: res.data.id } })
    } catch (e) {
        alert('保存相册失败')
    }
}

const getRecIcon = (type) => {
    switch(type) {
        case 'person': return User
        case 'location': return MapPin
        case 'event': return Calendar
        default: return Sparkles
    }
}
</script>

<template>
  <div class="h-full overflow-y-auto pt-6 px-4 sm:px-8 pb-12">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">探索</h1>
      <p class="text-gray-500 mt-1">发现照片中的美好时刻与故事</p>
    </div>

    <!-- Memories Section -->
    <div class="mb-12">
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
                <Clock class="text-blue-500" />
                <h2 class="text-xl font-bold text-gray-800">美好回忆</h2>
            </div>
        </div>
        
        <div v-if="loadingMemories && memories.length === 0" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>

        <div v-else-if="memories.length > 0" class="flex gap-4 overflow-x-auto pb-4 snap-x">
            <div 
                v-for="memory in memories" 
                :key="memory.id"
                class="min-w-[280px] w-[280px] bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer group snap-start"
                @click="router.push({ name: 'memory-detail', params: { id: memory.id } })"
            >
                <div class="aspect-[4/5] bg-gray-100 relative overflow-hidden">
                    <img 
                        v-if="memory.cover"
                        :src="memory.cover.thumbnail" 
                        class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                    />
                    <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-80"></div>
                    
                    <div class="absolute bottom-4 left-4 right-4 text-white">
                        <h3 class="font-bold text-lg leading-tight mb-1">{{ memory.title }}</h3>
                        <p class="text-xs opacity-80 line-clamp-2">{{ memory.description }}</p>
                    </div>

                    <div class="absolute top-3 right-3 bg-white/20 backdrop-blur-md text-white text-xs px-2 py-1 rounded-full">
                         {{ memory.photo_count }} 张
                    </div>
                </div>
            </div>
        </div>

        <div v-else class="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <Clock class="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 class="text-lg font-medium text-gray-900">暂无回忆</h3>
            <p class="text-gray-500">上传更多照片，精彩回忆即将呈现</p>
        </div>
    </div>

    <!-- Recommendations Section -->
    <div class="mb-12">
        <div class="flex items-center gap-2 mb-4">
            <Sparkles class="text-amber-500" />
            <h2 class="text-xl font-bold text-gray-800">智能相册推荐</h2>
        </div>
        
        <div v-if="loadingRecs && recommendations.length === 0" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>

        <div v-else-if="recommendations.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
            <div 
                v-for="rec in recommendations" 
                :key="rec.id"
                class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow group flex flex-col"
            >
                <div class="aspect-video bg-gray-100 relative overflow-hidden">
                    <img 
                        v-if="rec.cover_url"
                        :src="rec.cover_url" 
                        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
                        <Image :size="32" />
                    </div>
                    
                    <div class="absolute top-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded-full backdrop-blur-sm">
                        {{ rec.photo_count }} 张照片
                    </div>
                </div>
                
                <div class="p-4 flex-1 flex flex-col">
                    <div class="flex items-start justify-between gap-2 mb-2">
                        <h3 class="font-bold text-gray-900 line-clamp-1">{{ rec.title }}</h3>
                        <component :is="getRecIcon(rec.type)" :size="16" class="text-gray-400 flex-shrink-0 mt-1" />
                    </div>
                    <p class="text-sm text-gray-500 line-clamp-2 mb-4 flex-1">{{ rec.description }}</p>
                    
                    <button 
                        @click="saveRecommendation(rec)"
                        class="w-full py-2 bg-blue-50 text-blue-600 font-medium rounded-lg hover:bg-blue-100 transition-colors text-sm"
                    >
                        保存到相册
                    </button>
                </div>
            </div>
        </div>

        <div v-else class="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <Sparkles class="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 class="text-lg font-medium text-gray-900">暂无推荐</h3>
            <p class="text-gray-500 mb-4">系统正在分析您的照片，请稍候...</p>
            <div class="text-sm text-gray-400 space-y-1">
                <p>生成条件：</p>
                <p>• 人物精选：运行人脸识别且单人照片 > 5 张</p>
                <p>• 时间记忆：单日拍摄照片 > 10 张</p>
                <p>• 地点之旅：照片包含 GPS 信息且同一地点 > 5 张</p>
            </div>
        </div>
    </div>
  </div>
</template>
