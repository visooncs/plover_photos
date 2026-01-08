import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePersonStore = defineStore('person', () => {
  const people = ref([])
  const currentPerson = ref(null)
  const nextUrl = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchPeople(url = '/api/people/') {
    loading.value = true
    try {
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch people')
      const data = await response.json()
      
      if (data.results) {
        if (url.includes('page=')) {
          people.value = [...people.value, ...data.results]
        } else {
          people.value = data.results
        }
        nextUrl.value = data.next
      } else {
        people.value = data
        nextUrl.value = null
      }
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (nextUrl.value && !loading.value) {
      await fetchPeople(nextUrl.value)
    }
  }

  async function fetchPerson(id) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch(`/api/people/${id}/`)
      if (!response.ok) throw new Error('Failed to fetch person')
      currentPerson.value = await response.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function clearCurrentPerson() {
    currentPerson.value = null
  }

  async function updatePersonName(id, name) {
    try {
      const response = await fetch(`/api/people/${id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      })
      if (!response.ok) throw new Error('Failed to update name')
      const updatedPerson = await response.json()
      
      // Update local state
      if (currentPerson.value && currentPerson.value.id === id) {
        currentPerson.value.name = updatedPerson.name
      }
      const index = people.value.findIndex(p => p.id === id)
      if (index !== -1) {
        people.value[index].name = updatedPerson.name
      }
      return updatedPerson
    } catch (e) {
      throw e
    }
  }

  async function setCover(personId, photoId) {
    try {
      const response = await fetch(`/api/people/${personId}/set_cover/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ photo_id: photoId }),
      })
      if (!response.ok) {
          const err = await response.json()
          throw new Error(err.error || 'Failed to set cover')
      }
      const data = await response.json()
      
      // Update local state
      if (currentPerson.value && currentPerson.value.id === personId) {
        currentPerson.value.face_url = data.face_url
      }
      return data
    } catch (e) {
      throw e
    }
  }

  async function removePhoto(personId, photoId) {
    try {
      const response = await fetch(`/api/people/${personId}/remove_photo/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ photo_id: photoId }),
      })
      if (!response.ok) {
          const err = await response.json()
          throw new Error(err.error || 'Failed to remove photo')
      }
      return await response.json()
    } catch (e) {
      throw e
    }
  }

  return {
    people,
    currentPerson,
    nextUrl,
    loading,
    error,
    fetchPeople,
    loadMore,
    fetchPerson,
    clearCurrentPerson,
    updatePersonName,
    setCover,
    removePhoto
  }
})
