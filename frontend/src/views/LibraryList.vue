<script setup>
import { ref, onMounted } from 'vue'
import { Folder, FolderPlus, RefreshCw, Trash2, HardDrive, AlertCircle, FolderSync } from 'lucide-vue-next'
import axios from 'axios'

const libraries = ref([])
const loading = ref(false)
const showAddModal = ref(false)
const newLibraryPath = ref('')
const adding = ref(false)
const error = ref(null)

const fetchLibraries = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/libraries/')
    // Handle both paginated and non-paginated responses
    if (response.data && Array.isArray(response.data.results)) {
        libraries.value = response.data.results
    } else if (Array.isArray(response.data)) {
        libraries.value = response.data
    } else {
        console.warn('Unexpected API response format:', response.data)
        libraries.value = []
    }
  } catch (e) {
    error.value = '获取库列表失败'
    console.error(e)
  } finally {
    loading.value = false
  }
}

const addLibrary = async () => {
  if (!newLibraryPath.value) return
  
  adding.value = true
  try {
    await axios.post('/api/libraries/', {
      name: newLibraryPath.value.split(/[\\/]/).pop() || 'New Library',
      path: newLibraryPath.value
    })
    newLibraryPath.value = ''
    showAddModal.value = false
    fetchLibraries()
  } catch (e) {
    alert('添加库失败: ' + (e.response?.data?.path?.[0] || e.message))
  } finally {
    adding.value = false
  }
}

const deleteLibrary = async (id) => {
  // if (!confirm('确定要删除这个库吗？库中的照片记录将被删除（原始文件不会被删除）。')) return
  
  try {
    await axios.delete(`/api/libraries/${id}/`)
    fetchLibraries()
  } catch (e) {
    alert('删除失败')
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'scanning': return 'text-blue-600 bg-blue-50 border-blue-200'
    case 'completed': return 'text-green-600 bg-green-50 border-green-200'
    case 'failed': return 'text-red-600 bg-red-50 border-red-200'
    case 'paused': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    default: return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

const getStatusText = (status) => {
    switch (status) {
        case 'pending': return '等待中'
        case 'scanning': return '扫描中'
        case 'completed': return '已完成'
        case 'failed': return '失败'
        case 'paused': return '已暂停'
        default: return status
    }
}

onMounted(() => {
  fetchLibraries()
  // Simple polling for status updates every 5 seconds
  setInterval(fetchLibraries, 5000)
})
</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <div class="p-6 border-b border-gray-100 flex justify-between items-center flex-shrink-0">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <HardDrive class="text-blue-600" />
            库管理
        </h1>
        <p class="text-gray-500 mt-1">管理照片来源目录，系统将自动扫描这些目录中的照片和视频</p>
      </div>
      <div class="flex gap-2">
        <button 
          @click="fetchLibraries"
          class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="刷新列表"
        >
          <RefreshCw :size="20" :class="{ 'animate-spin': loading }" />
        </button>
        <button 
          @click="showAddModal = true"
          class="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors shadow-sm"
        >
          <FolderPlus :size="20" />
          <span>添加目录</span>
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2">
            <FolderSync class="text-blue-600" :size="20" />
            照片库目录
        </h2>
      </div>

    <!-- Error State -->
    <div v-if="error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
      <AlertCircle :size="20" />
      <p>{{ error }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading && libraries.length === 0" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="libraries.length === 0" class="text-center py-16 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
      <Folder class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-gray-900">暂无照片库</h3>
      <p class="text-gray-500 mt-2 mb-6">添加一个本地目录开始扫描照片</p>
      <button 
        @click="showAddModal = true"
        class="text-blue-600 hover:text-blue-700 font-medium"
      >
        立即添加
      </button>
    </div>

    <!-- Library List -->
    <div v-else class="space-y-4">
      <div 
        v-for="lib in libraries" 
        :key="lib.id"
        class="bg-white rounded-xl border border-gray-200 p-6 flex flex-col sm:flex-row gap-6 shadow-sm hover:shadow-md transition-shadow"
      >
        <div class="flex-shrink-0 flex items-start">
            <div class="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
                <Folder :size="24" />
            </div>
        </div>
        
        <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-4">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 truncate" :title="lib.path">
                        {{ lib.name }}
                    </h3>
                    <p class="text-sm text-gray-500 font-mono mt-1 break-all">{{ lib.path }}</p>
                </div>
                <span 
                    class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border"
                    :class="getStatusColor(lib.scan_status)"
                >
                    <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse" v-if="lib.scan_status === 'scanning'"></span>
                    {{ getStatusText(lib.scan_status) }}
                </span>
            </div>

            <div class="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                    <p class="text-gray-500">总文件</p>
                    <p class="font-medium text-gray-900">{{ lib.total_files || 0 }}</p>
                </div>
                <div>
                    <p class="text-gray-500">已处理</p>
                    <p class="font-medium text-gray-900">{{ lib.processed_files || 0 }}</p>
                </div>
                <div>
                    <p class="text-gray-500">上次扫描</p>
                    <p class="font-medium text-gray-900">
                        {{ lib.last_scanned_at ? new Date(lib.last_scanned_at).toLocaleString() : '从未' }}
                    </p>
                </div>
                <div v-if="lib.scan_error" class="text-red-600 col-span-2 sm:col-span-1">
                    <p class="text-gray-500">错误信息</p>
                    <p class="font-medium truncate" :title="lib.scan_error">{{ lib.scan_error }}</p>
                </div>
            </div>

            <!-- Progress Bar -->
            <div v-if="lib.scan_status === 'scanning'" class="mt-4">
                <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div 
                        class="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        :style="{ width: `${lib.total_files ? (lib.processed_files / lib.total_files * 100) : 0}%` }"
                    ></div>
                </div>
                <p class="text-xs text-gray-500 mt-1 text-right">
                    {{ lib.total_files ? Math.round(lib.processed_files / lib.total_files * 100) : 0 }}%
                </p>
            </div>
        </div>

        <div class="flex items-start gap-2 border-l border-gray-100 pl-6 ml-2">
            <button 
                @click="deleteLibrary(lib.id)"
                class="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="删除库"
            >
                <Trash2 :size="20" />
            </button>
        </div>
      </div>
    </div>

    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
            <div class="p-6">
                <h3 class="text-lg font-bold text-gray-900 mb-4">添加照片库</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">文件夹路径</label>
                        <input 
                            v-model="newLibraryPath"
                            type="text" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
                            placeholder="例如: D:\Photos"
                            @keyup.enter="addLibrary"
                        >
                        <p class="text-xs text-gray-500 mt-1">请输入包含照片和视频的绝对路径</p>
                    </div>
                </div>
            </div>
            <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3">
                <button 
                    @click="showAddModal = false"
                    class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    取消
                </button>
                <button 
                    @click="addLibrary"
                    :disabled="adding || !newLibraryPath"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    <div v-if="adding" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    确认添加
                </button>
            </div>
        </div>
    </div>

  </div>
</template>
