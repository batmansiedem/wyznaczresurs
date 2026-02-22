<template>
  <MainLayout v-if="userStore.isLoggedIn" />
  <LandingLayout v-else />
</template>

<script setup>
import { useUserStore } from 'stores/user-store'
import MainLayout from './MainLayout.vue'
import LandingLayout from './LandingLayout.vue'

const userStore = useUserStore()
</script>
