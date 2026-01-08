<script setup>
import { RouterView } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import UploadProgress from '@/components/upload/UploadProgress.vue'
import DropZone from '@/components/upload/DropZone.vue'
</script>

<template>
  <MainLayout>
    <RouterView />
    <UploadProgress />
    <DropZone />
  </MainLayout>
</template>

<style>
/* 移除全局样式，改用 style.css 和 Tailwind */
</style>
