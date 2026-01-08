import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ExploreView from '../views/ExploreView.vue'
import AlbumList from '../views/AlbumList.vue'
import AlbumDetail from '../views/AlbumDetail.vue'
import MemoryDetail from '../views/MemoryDetail.vue'
import PersonList from '../views/PersonList.vue'
import PersonDetail from '../views/PersonDetail.vue'
import SimilarPeople from '../views/SimilarPeople.vue'
import SearchResults from '../views/SearchResults.vue'
import MapView from '../views/MapView.vue'
import PlacesView from '../views/PlacesView.vue'
import LibraryList from '../views/LibraryList.vue'
import TrashView from '../views/TrashView.vue'
import Maintenance from '../views/Maintenance.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/trash',
      name: 'trash',
      component: TrashView
    },
    {
      path: '/explore',
      name: 'explore',
      component: ExploreView
    },
    {
      path: '/places',
      name: 'places',
      component: PlacesView
    },
    {
      path: '/libraries',
      name: 'libraries',
      component: LibraryList
    },
    {
      path: '/maintenance',
      name: 'maintenance',
      component: Maintenance
    },
    {
      path: '/search',
      name: 'search',
      component: SearchResults
    },
    {
      path: '/map',
      name: 'map',
      component: MapView
    },
    {
      path: '/albums',
      name: 'albums',
      component: AlbumList
    },
    {
      path: '/albums/:id',
      name: 'album-detail',
      component: AlbumDetail
    },
    {
      path: '/memories/:id',
      name: 'memory-detail',
      component: MemoryDetail
    },
    {
      path: '/people',
      name: 'people',
      component: PersonList
    },
    {
      path: '/people/:id',
      name: 'person-detail',
      component: PersonDetail
    },
    {
      path: '/people/:id/similar',
      name: 'person-similar',
      component: SimilarPeople
    }
  ]
})

export default router
