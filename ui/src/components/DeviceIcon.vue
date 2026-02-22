<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 100 100"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    class="device-icon"
  >
    <defs>
      <linearGradient :id="'grad-' + slug" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color: currentColor; stop-opacity: 1" />
        <stop offset="100%" style="stop-color: currentColor; stop-opacity: 0.7" />
      </linearGradient>
    </defs>

    <g :fill="'url(#grad-' + slug + ')'">
      <!-- Wciągnik (Hoist) -->
      <template v-if="slug === 'wciagnik'">
        <rect x="30" y="20" width="40" height="30" rx="2" />
        <rect x="35" y="15" width="30" height="5" rx="1" />
        <path d="M50 50 V75" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
        <path d="M45 75 Q50 85 55 75" stroke="currentColor" stroke-width="4" fill="none" />
      </template>

      <!-- Wciągarka (Winch) - POPRAWIONA (Bęben, napęd, lina) -->
      <template v-else-if="slug === 'wciagarka'">
        <rect x="15" y="35" width="12" height="30" rx="2" /> <!-- Silnik -->
        <rect x="27" y="40" width="6" height="20" /> <!-- Przekładnia -->
        <rect x="33" y="30" width="40" height="40" rx="2" fill-opacity="0.3" /> <!-- Bęben -->
        <path d="M33 35 H73 M33 40 H73 M33 45 H73 M33 50 H73 M33 55 H73 M33 60 H73 M33 65 H73" stroke="currentColor" stroke-width="1.5" opacity="0.6" /> <!-- Lina na bębnie -->
        <rect x="73" y="35" width="12" height="30" rx="2" /> <!-- Łożyskowanie -->
        <path d="M53 30 V15 H85" stroke="currentColor" stroke-width="3" stroke-linecap="round" fill="none" /> <!-- Lina wychodząca -->
        <rect x="15" y="70" width="70" height="5" rx="1" /> <!-- Podstawa -->
      </template>

      <!-- Suwnica (Overhead Crane) -->
      <template v-else-if="slug === 'suwnica'">
        <rect x="10" y="25" width="80" height="10" rx="2" />
        <rect x="15" y="20" width="5" height="20" rx="1" />
        <rect x="80" y="20" width="5" height="20" rx="1" />
        <rect x="40" y="30" width="20" height="10" rx="1" />
        <path d="M50 40 V65" stroke="currentColor" stroke-width="3" />
        <path d="M45 65 Q50 75 55 65" stroke="currentColor" stroke-width="3" fill="none" />
      </template>

      <!-- Żuraw (Tower Crane) -->
      <template v-else-if="slug === 'zuraw'">
        <rect x="42" y="10" width="6" height="80" rx="1" />
        <rect x="10" y="25" width="85" height="6" rx="1" />
        <rect x="15" y="20" width="15" height="15" rx="1" />
        <path d="M80 31 V60" stroke="currentColor" stroke-width="2" />
        <path d="M77 60 Q80 68 83 60" stroke="currentColor" stroke-width="2" fill="none" />
        <rect x="35" y="85" width="20" height="5" rx="1" />
      </template>

      <!-- Żuraw przeładunkowy (Loader Crane / HDS) - POPRAWIONA (Z podporami i ramionami) -->
      <template v-else-if="slug === 'zuraw_przeladunkowy'">
        <rect x="10" y="72" width="80" height="12" rx="2" fill-opacity="0.4" /> <!-- Podwozie -->
        <circle cx="25" cy="85" r="7" /> <circle cx="75" cy="85" r="7" /> <!-- Koła -->
        <rect x="45" y="60" width="10" height="12" /> <!-- Podstawa żurawia -->
        <rect x="15" y="72" width="4" height="20" rx="1" /> <!-- Podpora lewa -->
        <rect x="81" y="72" width="4" height="20" rx="1" /> <!-- Podpora prawa -->
        <path d="M50 60 V35 L75 30 L90 50" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none" /> <!-- Ramię -->
        <path d="M60 33 L75 30" stroke="white" stroke-width="2" opacity="0.3" /> <!-- Teleskop -->
        <path d="M90 50 V60" stroke="currentColor" stroke-width="2" stroke-dasharray="2 2" /> <!-- Lina/Hak -->
        <path d="M87 60 Q90 68 93 60" stroke="currentColor" stroke-width="2" fill="none" />
      </template>

      <!-- Układnica magazynowa (Stacker Crane) -->
      <template v-else-if="slug === 'ukladnica_magazynowa'">
        <rect x="30" y="10" width="5" height="80" rx="1" />
        <rect x="65" y="10" width="5" height="80" rx="1" />
        <rect x="25" y="85" width="50" height="5" rx="1" />
        <rect x="30" y="40" width="40" height="10" rx="2" />
        <path d="M70 45 H85" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
      </template>

      <!-- Dźwignik (Jack / Lift Table) -->
      <template v-else-if="slug === 'dzwignik'">
        <rect x="20" y="30" width="60" height="8" rx="2" />
        <path d="M30 38 L70 72 M70 38 L30 72" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
        <rect x="20" y="72" width="60" height="8" rx="2" />
      </template>

      <!-- Hakowiec (Hook Loader) - POPRAWIONA (Ramię hakowe L i kontener) -->
      <template v-else-if="slug === 'hakowiec'">
        <rect x="10" y="75" width="80" height="10" rx="1" fill-opacity="0.3" /> <!-- Podwozie -->
        <rect x="15" y="60" width="20" height="15" rx="1" /> <!-- Kabina -->
        <circle cx="30" cy="85" r="6" /> <circle cx="75" cy="85" r="6" /> <!-- Koła -->
        <path d="M40 75 L65 35 L80 40" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none" /> <!-- Ramię L -->
        <path d="M80 40 L78 50" stroke="currentColor" stroke-width="3" stroke-linecap="round" fill="none" /> <!-- Hak -->
        <rect x="40" y="55" width="45" height="20" rx="1" fill-opacity="0.2" stroke="currentColor" stroke-width="1" stroke-dasharray="2 2" /> <!-- Kontener (zarys) -->
      </template>

      <!-- Podnośnik samochodowy (Car Lift) -->
      <template v-else-if="slug === 'podnosnik_samochodowy'">
        <rect x="20" y="15" width="6" height="75" rx="1" />
        <rect x="74" y="15" width="6" height="75" rx="1" />
        <rect x="20" y="45" width="60" height="5" rx="1" />
        <path d="M30 40 H70 L75 45 H25 L30 40Z" fill="currentColor" opacity="0.3" />
        <rect x="15" y="85" width="70" height="5" rx="1" />
      </template>

      <!-- Autotransporter - POPRAWIONA (Profesjonalna laweta piętrowa) -->
      <template v-else-if="slug === 'autotransporter'">
        <rect x="8" y="72" width="84" height="12" rx="2" fill-opacity="0.4" /> <!-- Podwozie główne -->
        <rect x="10" y="58" width="18" height="16" rx="2" /> <!-- Kabina -->
        <rect x="12" y="62" width="10" height="6" fill="white" fill-opacity="0.3" /> <!-- Szyba kabiny -->
        <circle cx="20" cy="85" r="7" /> <circle cx="68" cy="85" r="7" /> <circle cx="82" cy="85" r="7" /> <!-- Koła -->
        
        <!-- Górny pokład z kątem nachylenia -->
        <path d="M30 42 H92 L88 48 H30 Z" fill-opacity="0.8" /> 
        <!-- Dolny pokład -->
        <rect x="30" y="68" width="58" height="4" rx="1" />
        
        <!-- Słupki hydrauliczne/konstrukcyjne -->
        <rect x="40" y="42" width="3" height="30" />
        <rect x="65" y="42" width="3" height="30" />
        <rect x="85" y="42" width="3" height="30" />
        
        <!-- Najazdy tylne -->
        <path d="M92 42 L98 72 H94 L88 42 Z" fill-opacity="0.3" />
      </template>

      <!-- Podest ruchomy (Mobile Platform) -->
      <template v-else-if="slug === 'podest_ruchomy'">
        <rect x="30" y="75" width="40" height="12" rx="2" />
        <circle cx="35" cy="87" r="5" fill="currentColor" />
        <circle cx="65" cy="87" r="5" fill="currentColor" />
        <path d="M50 75 L70 30" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
        <rect x="60" y="15" width="25" height="15" rx="2" stroke="currentColor" stroke-width="2" fill="none" />
      </template>

      <!-- Podest załadowczy (Tail Lift) - Uproszczona mechanika (Ramiona i platforma) -->
      <template v-else-if="slug === 'podest_zaladowczy'">
        <rect x="10" y="15" width="12" height="70" rx="1" fill-opacity="0.2" /> <!-- Tył pojazdu -->
        <path d="M22 45 L55 45 M22 65 L55 65" stroke="currentColor" stroke-width="6" stroke-linecap="round" /> <!-- Ramiona mechanizmu -->
        <rect x="55" y="40" width="35" height="6" rx="1" fill-opacity="1" /> <!-- Platforma (płyta) -->
        <rect x="55" y="40" width="6" height="30" rx="1" fill="currentColor" /> <!-- Pionowy łącznik -->
        <circle cx="22" cy="45" r="3" fill="currentColor" /> <!-- Zawiasy -->
        <circle cx="22" cy="65" r="3" fill="currentColor" />
      </template>

      <!-- Wózek jezdniowy (Forklift) -->
      <template v-else-if="slug === 'wozek_jezdniowy'">
        <path d="M20 80 H60 V55 H35 L20 70 Z" fill="currentColor" />
        <rect x="65" y="20" width="5" height="65" rx="1" />
        <path d="M70 70 H90 V75 H70 Z" fill="currentColor" />
        <circle cx="30" cy="85" r="7" fill="currentColor" />
        <circle cx="55" cy="85" r="7" fill="currentColor" />
      </template>

      <!-- Wózek specjalizowany -->
      <template v-else-if="slug === 'wozek_specjalizowany'">
        <path d="M15 80 H55 V50 H30 L15 70 Z" fill="currentColor" />
        <rect x="60" y="15" width="4" height="70" rx="1" />
        <rect x="70" y="15" width="4" height="70" rx="1" />
        <rect x="60" y="40" width="25" height="8" rx="1" />
        <circle cx="25" cy="85" r="7" fill="currentColor" />
        <circle cx="50" cy="85" r="7" fill="currentColor" />
      </template>

      <!-- Dźwig (Elevator) - POPRAWIONA (Drzwi szybu, panel, piętro) -->
      <template v-else-if="slug === 'dzwig'">
        <rect x="20" y="10" width="60" height="80" rx="2" stroke="currentColor" stroke-width="3" fill-opacity="0.1" /> <!-- Szyb -->
        <rect x="30" y="20" width="20" height="70" stroke="currentColor" stroke-width="1" fill-opacity="0.3" /> <!-- Lewe drzwi -->
        <rect x="50" y="20" width="20" height="70" stroke="currentColor" stroke-width="1" fill-opacity="0.3" /> <!-- Prawe drzwi -->
        <path d="M50 20 V90" stroke="currentColor" stroke-width="1" /> <!-- Szczelina drzwi -->
        <rect x="72" y="45" width="5" height="10" rx="1" /> <!-- Panel przyzywowy -->
        <circle cx="74.5" cy="48" r="1" fill="white" /> <!-- Przycisk góra -->
        <circle cx="74.5" cy="52" r="1" fill="white" /> <!-- Przycisk dół -->
        <rect x="40" y="12" width="20" height="6" rx="1" fill="black" fill-opacity="0.8" /> <!-- Wyświetlacz -->
        <path d="M48 15 L52 15" stroke="red" stroke-width="1" opacity="0.8" /> <!-- "Liczba" na wyświetlaczu -->
      </template>

      <!-- Winda dekarska (Inclined Lift) -->
      <template v-else-if="slug === 'winda_dekarska'">
        <path d="M20 90 L70 15" stroke="currentColor" stroke-width="6" stroke-linecap="round" />
        <path d="M28 90 L78 15" stroke="currentColor" stroke-width="6" stroke-linecap="round" />
        <path d="M30 75 H40 M40 60 H50 M50 45 H60 M60 30 H70" stroke="white" stroke-width="2" />
        <rect x="55" y="25" width="25" height="8" rx="1" transform="rotate(-56 55 25)" fill="currentColor" />
      </template>

      <!-- Mechanizm podnoszenia -->
      <template v-else-if="slug === 'mech_podnoszenia'">
        <circle cx="50" cy="40" r="25" stroke="currentColor" stroke-width="4" fill="none" />
        <path d="M50 25 V55" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
        <path d="M40 45 L50 55 L60 45" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none" />
        <path d="M40 35 L50 25 L60 35" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none" />
      </template>

      <!-- Mechanizmy jazdy (Wspólny styl) -->
      <template v-else-if="slug.startsWith('mech_jazdy')">
        <rect x="20" y="40" width="60" height="20" rx="2" fill="currentColor" opacity="0.3" />
        <circle cx="35" cy="65" r="8" fill="currentColor" />
        <circle cx="65" cy="65" r="8" fill="currentColor" />
        <path d="M20 50 H80" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
        <path d="M70 40 L80 50 L70 60" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none" />
        <path d="M30 40 L20 50 L30 60" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none" />
      </template>

      <!-- Mechanizm zmiany wysięgu -->
      <template v-else-if="slug === 'mech_zmiany_wysiegu'">
        <path d="M20 80 Q50 20 85 40" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="round" />
        <path d="M75 30 L85 40 L75 50" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none" />
        <circle cx="20" cy="80" r="5" fill="currentColor" />
      </template>

      <!-- Mechanizm zmiany obrotu -->
      <template v-else-if="slug === 'mech_zmiany_obrotu'">
        <path d="M20 50 A30 30 0 1 1 80 50 A30 30 0 1 1 20 50" stroke="currentColor" stroke-width="4" stroke-dasharray="80 20" fill="none" />
        <path d="M75 40 L85 50 L75 60" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none" />
        <circle cx="50" cy="50" r="10" fill="currentColor" />
      </template>

      <!-- Default / Fallback -->
      <template v-else>
        <rect x="20" y="20" width="60" height="60" rx="10" stroke="currentColor" stroke-width="4" fill="none" />
        <path d="M40 40 L60 60 M60 40 L40 60" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
      </template>
    </g>
  </svg>
</template>

<script setup>
defineProps({
  slug: { type: String, required: true },
  size: { type: [Number, String], default: 64 },
})
</script>

<style scoped>
.device-icon {
  display: inline-block;
  vertical-align: middle;
  transition: transform 0.2s ease-in-out;
}
.device-icon:hover {
  transform: scale(1.05);
}
</style>
