import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useAlbumStore = defineStore('album', () => {
  const albums = ref([])
  const currentAlbum = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchAlbums() {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/albums/')
      const data = response.data
      albums.value = data.results || data
    } catch (e) {
      error.value = e.message || 'Failed to fetch albums'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchAlbum(id) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/albums/${id}/`)
      currentAlbum.value = response.data
    } catch (e) {
      error.value = e.message || 'Failed to fetch album'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  return {
    albums,
    currentAlbum,
    loading,
    error,
    fetchAlbums,
    fetchAlbum
  }
})
