import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUploadStore = defineStore('upload', () => {
  const uploads = ref([])
  const isUploading = computed(() => uploads.value.some(u => u.status === 'uploading'))
  const overallProgress = computed(() => {
    if (uploads.value.length === 0) return 0
    const total = uploads.value.reduce((acc, u) => acc + u.size, 0)
    const loaded = uploads.value.reduce((acc, u) => acc + (u.uploaded || 0), 0)
    return total === 0 ? 0 : Math.round((loaded / total) * 100)
  })

  // 添加文件到上传队列
  function addFiles(fileList) {
    for (const file of fileList) {
      // 简单去重 (可选)
      const id = Math.random().toString(36).substring(2, 9)
      uploads.value.push({
        id,
        file,
        name: file.name,
        size: file.size,
        status: 'pending', // pending, uploading, completed, error
        uploaded: 0,
        progress: 0,
        error: null
      })
    }
    processQueue()
  }

  // 处理队列
  async function processQueue() {
    const pending = uploads.value.filter(u => u.status === 'pending')
    // 限制并发数，例如 3
    const uploading = uploads.value.filter(u => u.status === 'uploading')
    
    if (uploading.length >= 3) return

    for (const task of pending) {
        if (uploading.length >= 3) break
        uploadFile(task)
    }
  }

  async function uploadFile(task) {
    task.status = 'uploading'
    
    const formData = new FormData()
    formData.append('file', task.file)
    // 如果有相册 ID 等参数可以在这里加

    try {
        const xhr = new XMLHttpRequest()
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                task.uploaded = e.loaded
                task.progress = Math.round((e.loaded / e.total) * 100)
            }
        })

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                task.status = 'completed'
                task.progress = 100
                task.uploaded = task.size
            } else {
                task.status = 'error'
                task.error = `HTTP ${xhr.status}`
            }
            processQueue() // 尝试下一个
        }

        xhr.onerror = () => {
            task.status = 'error'
            task.error = 'Network Error'
            processQueue()
        }

        xhr.open('POST', '/api/photos/', true)
        // CSRF handling if needed
        // xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken')) 
        xhr.send(formData)

    } catch (e) {
        task.status = 'error'
        task.error = e.message
        processQueue()
    }
  }

  function clearCompleted() {
    uploads.value = uploads.value.filter(u => u.status !== 'completed')
  }

  return {
    uploads,
    isUploading,
    overallProgress,
    addFiles,
    clearCompleted
  }
})
