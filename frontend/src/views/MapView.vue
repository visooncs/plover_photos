<template>
  <div class="flex-1 w-full relative min-h-[500px]">
    <div id="map" class="absolute inset-0 z-0"></div>
    
    <!-- Photo Preview Popup (Custom overlay if needed, or use Leaflet popup) -->
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { wgs2gcj, addChineseTileLayer } from '../utils/mapUtils'

// Fix Leaflet icon issue
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
})

const map = ref(null)
const markers = ref([])

onMounted(async () => {
  initMap()
  await fetchMarkers()
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})

const initMap = () => {
  // Default to China view or world view
  map.value = L.map('map').setView([35.8617, 104.1954], 4)

  // Use GaoDe Map (Amap) for Chinese support
  addChineseTileLayer(map.value)
  
  map.value.on('moveend', debounce(fetchMarkers, 300))
}

const debounce = (fn, delay) => {
  let timer = null
  return (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn(...args)
    }, delay)
  }
}

const fetchMarkers = async () => {
  try {
    if (!map.value) return
    
    // Get map bounds
    const bounds = map.value.getBounds()
    const zoom = map.value.getZoom()
    
    const params = new URLSearchParams({
        min_lat: bounds.getSouth(),
        max_lat: bounds.getNorth(),
        min_lng: bounds.getWest(),
        max_lng: bounds.getEast(),
        zoom: zoom
    })

    const response = await fetch(`/map/markers/?${params}`)
    if (!response.ok) throw new Error('Failed to fetch markers')
    const data = await response.json()
    
    // Clear existing markers
    markers.value.forEach(m => map.value.removeLayer(m))
    markers.value = []

    data.forEach(item => {
        let iconHtml = ''
        if (item.count > 1) {
            iconHtml = `
                <div class="relative group cursor-pointer">
                    <div class="w-12 h-12 rounded-lg border-2 border-white shadow-lg overflow-hidden bg-gray-100 relative z-10">
                        <img src="${item.thumb}" class="w-full h-full object-cover" />
                    </div>
                    <div class="absolute -top-2 -right-2 bg-blue-600 text-white text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full border-2 border-white z-20">
                        ${item.count}
                    </div>
                    <div class="absolute top-1 left-1 w-12 h-12 bg-white rounded-lg border shadow-sm -z-10 rotate-6 transform translate-x-1 translate-y-1"></div>
                </div>
            `
        } else {
            iconHtml = `
                <div class="w-10 h-10 rounded-lg border-2 border-white shadow-lg overflow-hidden bg-gray-100 hover:scale-110 transition-transform">
                    <img src="${item.thumb}" class="w-full h-full object-cover" />
                </div>
            `
        }

        const icon = L.divIcon({
            html: iconHtml,
            className: 'bg-transparent',
            iconSize: item.count > 1 ? [56, 56] : [40, 40],
            iconAnchor: item.count > 1 ? [28, 28] : [20, 20]
        })

        // Transform coordinates to GCJ-02 for Chinese map
        const [gLat, gLng] = wgs2gcj(item.lat, item.lng)

        const marker = L.marker([gLat, gLng], { icon })
            .addTo(map.value)
            .bindPopup(`
                <div class="w-48 p-1">
                    <div class="w-full h-32 rounded-lg overflow-hidden bg-gray-100 mb-2">
                         <img src="${item.preview}" class="w-full h-full object-cover">
                    </div>
                    <p class="text-xs text-gray-500 mb-1">${item.date}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-xs font-bold text-gray-700">${item.count} 张照片</span>
                        <a href="/photos/${item.id}" class="text-xs text-white bg-blue-600 px-2 py-1 rounded hover:bg-blue-700">查看</a>
                    </div>
                </div>
            `, {
                closeButton: false,
                className: 'rounded-xl overflow-hidden shadow-xl border-none'
            })
            
        // Zoom in on cluster click
        if (item.count > 1) {
            marker.on('click', (e) => {
                // 如果已经是最大缩放，显示 popup；否则放大
                if (map.value.getZoom() < 18) {
                    map.value.setView(e.latlng, map.value.getZoom() + 2)
                    // Don't show popup when zooming
                    marker.closePopup()
                }
            })
        }
            
        markers.value.push(marker)
    })
    
  } catch (e) {
    console.error('Failed to fetch markers', e)
  }
}
</script>

<style>
/* Leaflet z-index fix if needed */
.leaflet-pane {
    z-index: 0;
}
</style>