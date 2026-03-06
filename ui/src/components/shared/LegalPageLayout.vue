<template>
  <!-- ===== MAIN LAYOUT (zalogowani) — wyrównany jak każda inna strona dashboardu ===== -->
  <q-page v-if="isLoggedIn" padding class="container">
    <div class="calc-page-header">
      <h1 class="text-h4 text-weight-bolder text-primary q-my-none">{{ title }}</h1>
      <p class="text-subtitle1 text-grey-7 q-mb-none">{{ subtitle }}</p>
    </div>

    <div class="legal-content">
      <q-card flat bordered class="q-pa-lg">
        <slot />
      </q-card>
      <div class="text-center q-mt-lg">
        <q-btn outline color="primary" icon="arrow_back" label="Powrót" @click="router.back()" />
      </div>
    </div>
  </q-page>

  <!-- ===== LANDING LAYOUT (gość) — styl jak ContactPage / HelpPage ===== -->
  <q-page v-else class="lp">
    <section class="legal-hero text-white">
      <div class="lc q-mx-auto q-px-md">
        <div class="eyebrow eyebrow--light q-mb-sm">{{ eyebrow }}</div>
        <h1 class="page-h1">{{ title }}</h1>
        <p class="page-sub">{{ subtitle }}</p>
      </div>
    </section>

    <div class="lc lc--narrow q-mx-auto q-px-md q-py-xl">
      <q-card flat bordered class="q-pa-lg">
        <slot />
      </q-card>
      <div class="text-center q-mt-lg">
        <q-btn outline color="primary" icon="arrow_back" label="Powrót" @click="router.back()" />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from 'stores/user-store'

const router = useRouter()
const isLoggedIn = computed(() => useUserStore().isLoggedIn)

defineProps({
  icon:     { type: String, required: true },
  title:    { type: String, required: true },
  subtitle: { type: String, default: '' },
  eyebrow:  { type: String, default: 'Informacje prawne' },
})
</script>

<style scoped lang="scss">
@use "sass:color";

// ── Main layout ──────────────────────────────────────────────────────────────
// Treść ograniczona do 860px od lewej (jak tekst na innych stronach dashboardu)
.legal-content { max-width: 860px; }

// ── Landing layout ───────────────────────────────────────────────────────────
.lc          { max-width: 1200px; }
.lc--narrow  { max-width: 860px;  }   // węższy kontener dla treści prawnej

.legal-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(145deg, $primary 0%, color.adjust($primary, $lightness: -24%) 100%);
  padding: 56px 0 48px;
}

.eyebrow {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase; color: $primary;
}
.eyebrow--light { color: rgba(white, 0.6); }

.page-h1 {
  font-size: clamp(1.8rem, 3.5vw, 2.6rem); font-weight: 900;
  letter-spacing: -0.02em; margin: 0 0 12px; line-height: 1.1;
}
.page-sub { font-size: 1rem; line-height: 1.6; opacity: 0.65; margin: 0; }

// ── Wspólna typografia treści (slot) ─────────────────────────────────────────
:deep(section) { border-left: 3px solid #e3f2fd; padding-left: 16px; }
.body--dark :deep(section) { border-left-color: rgba($primary, 0.22); }
:deep(ol), :deep(ul) { line-height: 1.8; padding-left: 22px; margin-bottom: 8px; }
:deep(li)  { margin-bottom: 4px; }
:deep(p)   { line-height: 1.7; margin-bottom: 10px; }
:deep(code) {
  background: #f0f4ff; padding: 1px 5px; border-radius: 3px; font-size: 0.9em;
}
.body--dark :deep(code) { background: #1e2a38; }
</style>
