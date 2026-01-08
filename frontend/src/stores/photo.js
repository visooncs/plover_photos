import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { format, parseISO, isToday, isYesterday } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export const usePhotoStore = defineStore('photo', () => {
  const photos = ref([])
  const loading = ref(false)
  const error = ref(null)
  const nextUrl = ref(null)
  const count = ref(0)
  const selectedPhotoIds = ref(new Set())
  const isTrashMode = ref(false)
  
  // Lightbox state
  const lightboxVisible = ref(false)
  const currentPhotoIndex = ref(0)

  // ...

  function toggleSelection(photoId) {
      if (selectedPhotoIds.value.has(photoId)) {
          selectedPhotoIds.value.delete(photoId)
      } else {
          selectedPhotoIds.value.add(photoId)
      }
  }

  function clearSelection() {
      selectedPhotoIds.value.clear()
  }

  const currentPhoto = computed(() => {
      if (currentPhotoIndex.value >= 0 && currentPhotoIndex.value < photos.value.length) {
          return photos.value[currentPhotoIndex.value]
      }
      return null
  })

  function openLightbox(photoOrIndex) {
      if (typeof photoOrIndex === 'number') {
          currentPhotoIndex.value = photoOrIndex
      } else {
          const index = photos.value.findIndex(p => p.id === photoOrIndex.id)
          if (index !== -1) {
              currentPhotoIndex.value = index
          }
      }
      lightboxVisible.value = true
  }

  function closeLightbox() {
      lightboxVisible.value = false
  }
  
  function nextPhoto() {
      if (currentPhotoIndex.value < photos.value.length - 1) {
          currentPhotoIndex.value++
      }
  }
  
  function prevPhoto() {
      if (currentPhotoIndex.value > 0) {
          currentPhotoIndex.value--
      }
  }

  const groupedPhotos = computed(() => {
    const groups = {}
    photos.value.forEach(photo => {
      const dateStr = photo.captured_at || photo.created_at
      const date = dateStr ? parseISO(dateStr) : new Date()
      const dateKey = format(date, 'yyyy-MM-dd')
      if (!groups[dateKey]) {
        groups[dateKey] = { id: dateKey, date: date, title: getDateTitle(date), photos: [] }
      }
      groups[dateKey].photos.push(photo)
    })
    return Object.values(groups).sort((a, b) => b.date - a.date)
  })

  function getDateTitle(date) {
    if (isToday(date)) return '今天'
    if (isYesterday(date)) return '昨天'
    if (date.getFullYear() === new Date().getFullYear()) {
      return format(date, 'M月d日', { locale: zhCN })
    }
    return format(date, 'yyyy年M月d日', { locale: zhCN })
  }

  async function fetchPhotos(url = '/api/photos/', params = {}) {
    loading.value = true
    error.value = null
    
    // 构建 URL 参数
    let fetchUrl = url
    if (Object.keys(params).length > 0) {
        const urlObj = new URL(url, window.location.origin)
        Object.keys(params).forEach(key => {
            if (params[key]) {
                urlObj.searchParams.set(key, params[key])
            }
        })
        fetchUrl = urlObj.toString().replace(window.location.origin, '')
    }

    try {
      const response = await fetch(fetchUrl)
      if (!response.ok) throw new Error('Failed to fetch photos')
      const data = await response.json()
      
      // 如果是第一页，直接覆盖；如果是加载更多，追加
      // 判断是否是追加模式 (check if we are loading next page)
      // Standard DRF response: { results: [], next: '...', count: ... }
      
      if (data.results) {
          if (fetchUrl.includes('page=') && fetchUrl !== '/api/photos/') {
               photos.value = [...photos.value, ...data.results]
          } else {
               photos.value = data.results
          }
          if (data.next) {
            try {
                const nextUrlObj = new URL(data.next)
                nextUrl.value = nextUrlObj.pathname + nextUrlObj.search
            } catch (e) {
                // If data.next is already relative or invalid
                nextUrl.value = data.next
            }
          } else {
            nextUrl.value = null
          }
          count.value = data.count
      } else {
          // Maybe it's a list response (unlikely for standard viewset list, but possible)
          photos.value = Array.isArray(data) ? data : []
          nextUrl.value = null
          count.value = photos.value.length
      }
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function searchPhotos(query) {
    loading.value = true
    error.value = null
    nextUrl.value = null
    
    try {
      const response = await fetch(`/api/photos/search/?q=${encodeURIComponent(query)}`)
      if (!response.ok) throw new Error('Search failed')
      const data = await response.json()
      
      if (Array.isArray(data)) {
          photos.value = data
          count.value = data.length
      } else {
          photos.value = []
          count.value = 0
      }
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }
  
  async function loadMore() {
      if (nextUrl.value && !loading.value) {
          await fetchPhotos(nextUrl.value)
      }
  }

  function clearPhotos() {
    photos.value = []
    nextUrl.value = null
    count.value = 0
  }

  async function deletePhoto(id) {
    try {
        await axios.delete(`/api/photos/${id}/`)
        removePhotoFromList(id)
    } catch (e) {
        console.error("Delete failed", e)
        throw e
    }
  }

  async function restorePhoto(id) {
    try {
        await axios.post(`/api/photos/${id}/restore/`)
        removePhotoFromList(id)
    } catch (e) {
        console.error("Restore failed", e)
        throw e
    }
  }

  async function permanentDeletePhoto(id) {
    try {
        await axios.delete(`/api/photos/${id}/permanent_delete/`)
        removePhotoFromList(id)
    } catch (e) {
        console.error("Permanent delete failed", e)
        throw e
    }
  }

  async function emptyTrash() {
    try {
        await axios.delete('/api/photos/empty_trash/')
        photos.value = []
        count.value = 0
    } catch (e) {
        console.error("Empty trash failed", e)
        throw e
    }
  }

  function removePhotoFromList(id) {
    photos.value = photos.value.filter(p => p.id !== id)
    count.value--
    if (selectedPhotoIds.value.has(id)) {
        selectedPhotoIds.value.delete(id)
    }
  }

  return { 
      photos, 
      loading, 
      error, 
      clearPhotos, 
      fetchPhotos, 
      searchPhotos, 
      loadMore, 
      nextUrl, 
      count, 
      selectedPhotoIds, 
      isTrashMode, 
      toggleSelection, 
      clearSelection, 
      groupedPhotos, 
      lightboxVisible, 
      currentPhotoIndex, 
      currentPhoto, 
      openLightbox, 
      closeLightbox, 
      nextPhoto, 
      prevPhoto, 
      removePhotoFromList, 
      deletePhoto, 
      restorePhoto, 
      permanentDeletePhoto, 
      emptyTrash
  }
})
