<template>
  <q-layout view="hHh Lpr lFf">
    <q-header bordered :class="$q.dark.isActive ? 'bg-dark text-primary' : 'bg-white text-primary'">
      <q-toolbar class="q-py-sm q-px-md">
        <q-btn dense flat round icon="menu" @click="toggleDrawer" class="q-mr-sm" />

        <q-toolbar-title class="text-weight-bolder">
          wyznacz<span class="text-secondary">resurs</span>.com
        </q-toolbar-title>

        <q-space />

        <div v-if="userStore.user" class="row items-center q-gutter-sm">
          <div class="text-right gt-xs q-mr-md">
            <div class="text-weight-bold" :class="$q.dark.isActive ? 'text-white' : 'text-dark'">{{ displayName }}</div>
            <div class="text-caption text-primary" style="line-height: 1">
              {{ userStore.isCompany ? 'Konto Firmowe' : 'Konto Prywatne' }}
            </div>
          </div>

          <q-btn flat round dense
            :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'"
            @click="$q.dark.toggle()"
            class="text-grey-7" />

          <q-btn-dropdown flat round dense icon="account_circle" class="text-primary">
            <q-list style="min-width: 200px" class="rounded-borders overflow-hidden">
              <q-item-label header class="text-weight-bold">Zarządzanie kontem</q-item-label>
              <q-item clickable v-close-popup to="/account">
                <q-item-section avatar><q-icon name="person" color="primary" /></q-item-section>
                <q-item-section>Moje dane</q-item-section>
              </q-item>
              <q-item clickable v-close-popup to="/change-password">
                <q-item-section avatar><q-icon name="lock" color="primary" /></q-item-section>
                <q-item-section>Zmień hasło</q-item-section>
              </q-item>
              <template v-if="userStore.user?.is_superuser">
                <q-separator />
                <q-item clickable v-close-popup to="/admin">
                  <q-item-section avatar><q-icon name="admin_panel_settings" color="red-7" /></q-item-section>
                  <q-item-section class="text-weight-bold text-red-7">Panel Admina</q-item-section>
                </q-item>
              </template>
              <q-separator />
              <q-item clickable v-close-popup @click="handleLogout" class="text-negative">
                <q-item-section avatar><q-icon name="logout" color="negative" /></q-item-section>
                <q-item-section class="text-weight-bold">Wyloguj się</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawerOpen" show-if-above bordered :class="$q.dark.isActive ? 'bg-dark' : 'bg-grey-1'">
      <q-list padding class="q-px-sm">
        <q-item-label header class="text-overline q-mt-sm">System</q-item-label>

        <q-item clickable to="/dashboard" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="dashboard" /></q-item-section>
          <q-item-section class="text-weight-medium">Pulpit</q-item-section>
        </q-item>

        <q-item clickable to="/calculators" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="calculate" /></q-item-section>
          <q-item-section class="text-weight-medium">Kalkulatory</q-item-section>
        </q-item>

        <q-item clickable to="/saved-results" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="history" /></q-item-section>
          <q-item-section class="text-weight-medium">Zapisane wyniki</q-item-section>
        </q-item>

        <q-item-label header class="text-overline q-mt-md">Konto</q-item-label>

        <q-item v-if="userStore.user" class="rounded-borders q-mb-sm bg-blue-1 text-primary">
          <q-item-section avatar><q-icon name="stars" color="primary" /></q-item-section>
          <q-item-section>
            <q-item-label class="text-weight-bold">Punkty Premium</q-item-label>
            <q-item-label caption class="text-primary">{{ userStore.user.premium }} pkt</q-item-label>
          </q-item-section>
        </q-item>

        <q-item clickable to="/invoices" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="receipt_long" /></q-item-section>
          <q-item-section class="text-weight-medium">Faktury</q-item-section>
        </q-item>

        <q-item clickable to="/pricing" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="payments" /></q-item-section>
          <q-item-section class="text-weight-medium">Cennik i punkty</q-item-section>
        </q-item>

        <!-- Panel admina — tylko dla superusera -->
        <template v-if="userStore.user?.is_superuser">
          <q-separator class="q-my-sm" />
          <q-item-label header class="text-overline text-red-7">Administrator</q-item-label>
          <q-item clickable to="/admin" active-class="text-red-7 bg-red-opacity" class="rounded-borders">
            <q-item-section avatar><q-icon name="admin_panel_settings" color="red-7" /></q-item-section>
            <q-item-section class="text-weight-bold text-red-7">Panel administratora</q-item-section>
          </q-item>
        </template>

        <q-separator class="q-my-md" />

        <q-item clickable to="/contact" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="email" /></q-item-section>
          <q-item-section class="text-weight-medium">Kontakt</q-item-section>
        </q-item>

        <q-item clickable to="/help" active-class="text-primary bg-primary-opacity" class="rounded-borders">
          <q-item-section avatar><q-icon name="help_outline" /></q-item-section>
          <q-item-section class="text-weight-medium">Pomoc / FAQ</q-item-section>
        </q-item>

        <!-- Linki prawne na dole -->
        <div class="q-mt-xl q-mb-sm q-px-sm legal-footer">
          <div class="text-caption text-grey-5 q-mb-xs">Informacje prawne</div>
          <div class="row q-gutter-xs">
            <router-link to="/regulamin" class="legal-link text-caption">Regulamin</router-link>
            <span class="text-grey-5 text-caption">·</span>
            <router-link to="/rodo" class="legal-link text-caption">RODO</router-link>
            <span class="text-grey-5 text-caption">·</span>
            <router-link to="/cookies" class="legal-link text-caption">Cookies</router-link>
          </div>
          <div class="text-caption text-grey-5 q-mt-xs">&copy; {{ new Date().getFullYear() }} wyznaczresurs.com</div>
        </div>
      </q-list>
    </q-drawer>

    <q-page-container>

      <!-- Breadcrumbs -->
      <q-toolbar v-if="breadcrumbs.length" dense class="q-px-md q-mt-md" style="min-height: 28px; padding-bottom: 6px">
        <q-breadcrumbs separator="›" :class="$q.dark.isActive ? 'text-grey-5' : 'text-grey-6'" active-color="primary">
          <q-breadcrumbs-el icon="home" :to="userStore.isLoggedIn ? '/dashboard' : '/'" />
          <q-breadcrumbs-el
            v-for="c in breadcrumbs"
            :key="c.label"
            :label="c.label"
            :to="c.to"
          />
        </q-breadcrumbs>
      </q-toolbar>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from 'stores/user-store'
import { useRouter, useRoute } from 'vue-router'

const drawerOpen = ref(false)
const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

// Slug → czytelna etykieta (bez importu dużego JSON w głównym bundlu)
function slugLabel(slug) {
  return slug.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase())
}

const breadcrumbs = computed(() => {
  const crumbs = route.meta.breadcrumbs
  if (!crumbs) return []
  // Kalkulator szczegółowy — wypełnij pustą etykietę nazwą z URL-a
  if (route.name === 'calculator' && route.params.slug) {
    return crumbs.map((c, i) => i === crumbs.length - 1 ? { ...c, label: slugLabel(route.params.slug) } : c)
  }
  return crumbs
})

const toggleDrawer = () => { drawerOpen.value = !drawerOpen.value }

const displayName = computed(() => {
  const u = userStore.user
  if (!u) return ''
  return u.is_company ? u.company_name : (u.first_name || u.email)
})

const handleLogout = async () => {
  await userStore.logout()
  router.push('/')
}
</script>

<style lang="scss">
.bg-primary-opacity {
  background-color: rgba(var(--q-primary-rgb), 0.08);
}
.bg-red-opacity {
  background-color: rgba(211, 47, 47, 0.08);
}
.legal-footer {
  border-top: 1px solid rgba(0,0,0,0.06);
  padding-top: 8px;
}
.legal-link {
  color: #9e9e9e;
  text-decoration: none;
  &:hover { color: #1565C0; text-decoration: underline; }
}
</style>
