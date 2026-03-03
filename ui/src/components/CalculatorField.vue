<template>
  <!-- NUMBER -->
  <q-input
    v-if="field.type === 'number'"
    :label="field.label + (field.required ? ' *' : '')"
    :model-value="numericValue"
    @update:model-value="updateValue"
    type="number"
    :step="field.step || 'any'"
    outlined color="primary"
    input-class="eng-value"
    :rules="field.required ? [val => (val !== null && val !== '') || 'Pole wymagane'] : []"
    lazy-rules="ondemand"
  >
    <template v-if="unitOptions.length > 1" v-slot:append>
      <!-- Klikalna pigułka jednostki — tylko masa i czas mają wiele jednostek -->
      <q-btn-dropdown
        :label="currentUnit"
        flat no-caps
        class="eng-unit-btn"
        dropdown-icon="expand_more"
        content-style="min-width:80px"
      >
        <q-list dense separator>
          <q-item
            v-for="u in unitOptions" :key="u.symbol"
            clickable v-close-popup dense
            @click="updateUnit(u.symbol)"
            :active="currentUnit === u.symbol"
            active-class="text-primary text-weight-bold"
          >
            <q-item-section class="text-center eng-value" style="font-size:0.85rem">
              {{ u.symbol }}
            </q-item-section>
          </q-item>
        </q-list>
      </q-btn-dropdown>
    </template>
    <template v-else-if="currentUnit" v-slot:append>
      <!-- Statyczny label jednostki -->
      <span class="eng-unit">{{ currentUnit }}</span>
    </template>
  </q-input>

  <!-- TEXT -->
  <q-input
    v-else-if="field.type === 'text'"
    :label="field.label + (field.required ? ' *' : '')"
    :model-value="modelValue"
    @update:model-value="updateValue"
    outlined color="primary"
    :rules="field.required ? [val => !!val || 'Pole wymagane'] : []"
    lazy-rules="ondemand"
  />

  <!-- SELECT -->
  <q-select
    v-else-if="field.type === 'select'"
    :label="field.label + (field.required ? ' *' : '')"
    :model-value="modelValue"
    @update:model-value="updateValue"
    :options="selectOptions"
    :option-value="hasLabeledOptions ? 'value' : undefined"
    :option-label="hasLabeledOptions ? 'label' : undefined"
    :emit-value="hasLabeledOptions"
    :map-options="hasLabeledOptions"
    outlined color="primary"
    :rules="field.required ? [val => !!val || 'Pole wymagane'] : []"
    lazy-rules="ondemand"
  />

  <!-- RADIO — inline z ramką, obsługa dark mode przez CSS -->
  <div
    v-else-if="field.type === 'radio'"
    class="calc-radio-field"
  >
    <div class="calc-radio-label">{{ field.label }}</div>
    <div class="row q-gutter-md q-mt-xs">
      <q-radio
        v-for="option in field.options"
        :key="option.value || option"
        :model-value="modelValue"
        @update:model-value="updateValue"
        :val="option.value || option"
        :label="option.label || option"
        color="primary"
      />
    </div>
  </div>

  <!-- DATE — z ikoną -->
  <q-input
    v-else-if="field.type === 'date'"
    :label="field.label + (field.required ? ' *' : '')"
    :model-value="modelValue"
    @update:model-value="updateValue"
    type="date"
    outlined color="primary"
    :rules="field.required ? [val => !!val || 'Pole wymagane'] : []"
    lazy-rules="ondemand"
  >
    <template v-slot:prepend>
      <q-icon name="event" color="primary" />
    </template>
  </q-input>

  <!-- TEXTAREA -->
  <q-input
    v-else-if="field.type === 'textarea'"
    :label="field.label + (field.required ? ' *' : '')"
    :model-value="modelValue"
    @update:model-value="updateValue"
    outlined color="primary"
    autogrow
  />

  <!-- GNP SELECTOR — wizualne karty A1–A8 -->
  <div v-else-if="field.type === 'gnp_selector'" class="gnp-selector-wrap">
    <div class="calc-radio-label q-mb-md">{{ field.label }}{{ field.required ? ' *' : '' }}</div>
    <div class="gnp-card-grid">
      <div
        v-for="card in GNP_CARDS"
        :key="card.value"
        :class="['gnp-card', { selected: modelValue === card.value }]"
        @click="updateValue(card.value)"
      >
        <div class="gnp-card-header">
          <div class="gnp-card-badge" :style="{ backgroundColor: card.color }">{{ card.value }}</div>
          <div class="gnp-card-fem">FEM {{ card.femCode }}</div>
          <q-icon v-if="modelValue === card.value" name="check_circle" size="20px" color="primary" class="gnp-selection-icon" />
        </div>
        <div class="gnp-card-body">
          <div class="gnp-card-title">{{ card.label_pl }}</div>
          <div class="gnp-card-sub">{{ card.sub_pl }}</div>
          
          <!-- Legacy norm mapping context -->
          <div class="gnp-norm-mapping q-mt-sm">
            <div v-if="card.pn79 !== '-'" class="norm-item">PN-79: <b>{{ card.pn79 }}</b></div>
            <div v-if="card.pn63 !== '-'" class="norm-item">PN-63: <b>{{ card.pn63 }}</b></div>
          </div>
        </div>
        <div class="gnp-card-footer" :style="{ color: card.color }">
          <div class="gnp-intensity-bar">
            <div v-for="n in 8" :key="n" class="bar-segment" :class="{ active: n <= card.intensity }" :style="{ backgroundColor: n <= card.intensity ? card.color : undefined }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- INSPECTION STATUS — nowoczesne kafelki oceny stanu technicznego -->
  <div v-else-if="field.type === 'inspection_status'" class="inspection-field">
    <div class="calc-radio-label q-mb-sm">{{ field.label }}{{ field.required ? ' *' : '' }}</div>
    <div class="inspection-grid">
      <div
        v-for="opt in getInspectionOptions(field.options)"
        :key="opt.value"
        :class="['inspection-tile', { selected: modelValue === opt.value }, `is-${opt.type}`]"
        @click="updateValue(opt.value)"
      >
        <q-icon :name="opt.icon" size="20px" class="q-mr-sm" />
        <div class="text-weight-bold">{{ opt.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Object], default: null },
  units: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue'])

// Karty GNP A1–A8 z opisami i kolorami wg intensywności obciążeń + mapowanie norm
const GNP_CARDS = [
  { value: 'A1', intensity: 1, label_pl: 'Okazjonalna', sub_pl: 'Bardzo lekkie',   color: '#2E7D32', femCode: '1',  pn91: 'A1', pn79: '-',    pn63: '-'    },
  { value: 'A2', intensity: 2, label_pl: 'Sporadyczna', sub_pl: 'Lekkie',          color: '#558B2F', femCode: '2',  pn91: 'A2', pn79: '-',    pn63: '-'    },
  { value: 'A3', intensity: 3, label_pl: 'Regularna',   sub_pl: 'Lekkie',          color: '#F9A825', femCode: '2/3',pn91: 'A3', pn79: '1',    pn63: '0'    },
  { value: 'A4', intensity: 4, label_pl: 'Regularna',   sub_pl: 'Umiarkowane',     color: '#EF6C00', femCode: '3/4',pn91: 'A4', pn79: '2',    pn63: '1'    },
  { value: 'A5', intensity: 5, label_pl: 'Intensywna',  sub_pl: 'Umiarkowane',     color: '#E65100', femCode: '4',  pn91: 'A5', pn79: '3',    pn63: '2'    },
  { value: 'A6', intensity: 6, label_pl: 'Intensywna',  sub_pl: 'Ciężkie',          color: '#BF360C', femCode: '4/5',pn91: 'A6', pn79: '4',    pn63: '2'    },
  { value: 'A7', intensity: 7, label_pl: 'B. intensywna', sub_pl: 'Ciężkie',       color: '#B71C1C', femCode: '5/6',pn91: 'A7', pn79: '5',    pn63: '3'    },
  { value: 'A8', intensity: 8, label_pl: 'Ekstremalna', sub_pl: 'B. ciężkie',    color: '#880E4F', femCode: '6',  pn91: 'A8', pn79: '6',    pn63: '4'    },
]

// Nowa logika dla kafelków inspekcji
function getInspectionOptions(opts) {
  if (!opts?.length) return []
  const normalized = opts.map(o => (typeof o === 'object' ? o : { label: o, value: o }))
  
  return normalized.map((opt) => {
    const label = opt.label.toLowerCase()
    let type, icon
    
    // Check for Negative states first (to avoid false positives like "Niesprawna" containing "sprawna")
    if (label.includes('nieprawidłowy') || 
        label.includes('niezgodne') || 
        label.includes('niezgodna') || 
        label.includes('niesprawna') || 
        label.includes('niesprawne') || 
        label.includes('nieszczelny') || 
        label.includes('uszkodzenia') || 
        label.includes('zły') || 
        label.includes('występują')) {
      type = 'negative'
      icon = 'report_problem'
    }
    // Neutral states
    else if (label.includes('nie dotyczy') || label.includes('n/d')) {
      type = 'neutral'
      icon = 'help_outline'
    }
    // Positive states
    else if (label.includes('prawidłowy') || 
             label.includes('brak uszkodzeń') || 
             label.includes('zgodne') || 
             label.includes('sprawna') || 
             label.includes('sprawne') || 
             label.includes('szczelny') || 
             label.includes('dobry')) {
      type = 'positive'
      icon = 'check_circle_outline'
    } 
    // Fallback
    else {
      type = 'neutral'
      icon = 'info_outline'
    }

    return { ...opt, type, icon }
  })
}

// Wartość numeryczna (obsługa dict {value, unit} i prostej liczby)
const numericValue = computed(() => {
  if (typeof props.modelValue === 'object' && props.modelValue !== null) {
    return props.modelValue.value
  }
  return props.modelValue
})

// Dropdown jednostki TYLKO dla masy i czasu — reszta (długość, prędkość) = statyczny label
const unitOptions = computed(() => {
  if (!['mass', 'time'].includes(props.field.unit_type)) return []
  return props.units[props.field.unit_type] || []
})

// Aktualnie wybrana jednostka (lub domyślna z definicji pola)
const currentUnit = computed(() => {
  if (typeof props.modelValue === 'object' && props.modelValue !== null && props.modelValue.unit) {
    return props.modelValue.unit
  }
  return props.field.default_unit || null
})

const updateValue = (newValue) => {
  if (props.field.type === 'number') {
    emit('update:modelValue', { value: newValue, unit: currentUnit.value })
  } else {
    emit('update:modelValue', newValue)
  }
}

const updateUnit = (newUnit) => {
  emit('update:modelValue', { value: numericValue.value, unit: newUnit })
}

// Czy opcje select to obiekty {label, value} (a nie proste stringi)
const hasLabeledOptions = computed(() => {
  const opts = props.field.options
  return Array.isArray(opts) && opts.length > 0 && typeof opts[0] === 'object'
})

// Opcje znormalizowane dla q-select
const selectOptions = computed(() => props.field.options || [])
</script>

<style scoped>
.calc-radio-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
}
.body--dark .calc-radio-label {
  color: rgba(255, 255, 255, 0.6);
}
.inspection-toggle {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  overflow: hidden;
}
.body--dark .inspection-toggle {
  border-color: rgba(255, 255, 255, 0.12);
}
</style>
