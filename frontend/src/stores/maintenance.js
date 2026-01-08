import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useMaintenanceStore = defineStore('maintenance', () => {
  const tasks = ref([])
  const schedules = ref([])
  const loading = ref(false)
  
  async function fetchTasks() {
    loading.value = true
    try {
      const [tasksRes, schedulesRes] = await Promise.all([
        fetch('/api/maintenance/'),
        fetch('/api/schedules/')
      ])
      
      if (tasksRes.ok) {
        const data = await tasksRes.json()
        tasks.value = data.results || data
      }
      
      if (schedulesRes.ok) {
        const data = await schedulesRes.json()
        schedules.value = data.results || data
      }
    } catch (e) {
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function createTask(name, params = {}) {
    try {
      const res = await fetch('/api/maintenance/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, params })
      })
      if (res.ok) {
        await fetchTasks()
        return await res.json()
      }
    } catch (e) {
      console.error(e)
    }
    return null
  }

  async function runTask(id) {
    try {
      const res = await fetch(`/api/maintenance/${id}/run/`, { method: 'POST' })
      if (res.ok) {
        await fetchTasks()
        return true
      }
    } catch (e) {
      console.error(e)
    }
    return false
  }
  
  async function deleteTask(id) {
    try {
        const res = await fetch(`/api/maintenance/${id}/`, { method: 'DELETE' })
        if (res.ok) {
            await fetchTasks()
        }
    } catch (e) {
        console.error(e)
    }
  }

  async function createSchedule(data) {
    try {
        const res = await fetch('/api/schedules/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        if (res.ok) {
            await fetchTasks()
            return true
        }
    } catch (e) { console.error(e) }
    return false
  }

  async function deleteSchedule(id) {
    try {
        const res = await fetch(`/api/schedules/${id}/`, { method: 'DELETE' })
        if (res.ok) {
            await fetchTasks()
        }
    } catch (e) { console.error(e) }
  }

  return {
    tasks,
    schedules,
    loading,
    fetchTasks,
    createTask,
    runTask,
    deleteTask,
    createSchedule,
    deleteSchedule
  }
})
