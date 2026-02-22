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
      <!-- Klikalna pigułka jednostki gdy dostępnych jest więcej niż jedna -->
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
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Object], default: null },
  units: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue'])

// Wartość numeryczna (obsługa dict {value, unit} i prostej liczby)
const numericValue = computed(() => {
  if (typeof props.modelValue === 'object' && props.modelValue !== null) {
    return props.modelValue.value
  }
  return props.modelValue
})

// Dostępne jednostki dla danego unit_type
const unitOptions = computed(() => {
  if (!props.field.unit_type) return []
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
