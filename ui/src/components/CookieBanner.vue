<template>
  <transition name="cookie-slide">
    <div v-if="show" class="cookie-banner" :class="{ 'cookie-banner--dark': $q.dark.isActive }">
      <div class="cookie-banner__inner">
        <div class="cookie-banner__icon">
          <q-icon name="cookie" size="2rem" color="primary" />
        </div>

        <div class="cookie-banner__text">
          <div class="cookie-banner__title">Ta strona używa plików cookies</div>
          <div class="cookie-banner__desc">
            Używamy niezbędnych plików cookies (sesja, CSRF, JWT) do prawidłowego działania serwisu.
            Nie stosujemy cookies reklamowych ani śledzących.
            <a href="/cookies" target="_blank" class="cookie-banner__link">Polityka cookies</a>
            &bull;
            <a href="/rodo" target="_blank" class="cookie-banner__link">Polityka prywatności</a>
          </div>
        </div>

        <div class="cookie-banner__actions">
          <q-btn
            outline color="grey-7" label="Tylko niezbędne" no-caps dense class="q-mr-sm"
            @click="acceptNecessary"
          />
          <q-btn
            unelevated color="primary" label="Akceptuję wszystkie" no-caps dense
            @click="acceptAll"
          />
        </div>

        <q-btn flat round dense icon="close" class="cookie-banner__close text-grey-6"
          @click="acceptNecessary" title="Zamknij" />
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const COOKIE_KEY = 'cookie_consent_v1'
const show = ref(false)

onMounted(() => {
  if (!localStorage.getItem(COOKIE_KEY)) {
    // Krótkie opóźnienie — żeby nie skakało przy ładowaniu
    setTimeout(() => { show.value = true }, 600)
  }
})

function acceptAll() {
  localStorage.setItem(COOKIE_KEY, 'all')
  show.value = false
}

function acceptNecessary() {
  localStorage.setItem(COOKIE_KEY, 'necessary')
  show.value = false
}
</script>

<style scoped>
.cookie-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  background: #fff;
  border-top: 2px solid #1565C0;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.12);
  padding: 14px 20px;
}
.cookie-banner--dark {
  background: #1d1d1d;
  border-top-color: #1976D2;
}
.cookie-banner__inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.cookie-banner__icon {
  flex-shrink: 0;
}
.cookie-banner__text {
  flex: 1;
  min-width: 220px;
}
.cookie-banner__title {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 3px;
}
.cookie-banner__desc {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
}
.cookie-banner--dark .cookie-banner__desc {
  color: #aaa;
}
.cookie-banner__link {
  color: #1565C0;
  text-decoration: underline;
}
.cookie-banner__actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.cookie-banner__close {
  flex-shrink: 0;
}

/* Animacja wjazdu od dołu */
.cookie-slide-enter-active,
.cookie-slide-leave-active {
  transition: transform 0.35s ease, opacity 0.35s ease;
}
.cookie-slide-enter-from,
.cookie-slide-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
