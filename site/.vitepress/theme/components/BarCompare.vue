<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    bad: number
    good: number
    unit?: string
    lowerIsBetter?: boolean
    badLabel?: string
    goodLabel?: string
    caption?: string
  }>(),
  { unit: '', lowerIsBetter: true, badLabel: 'Bad', goodLabel: 'Good', caption: undefined },
)

const max = computed(() => Math.max(props.bad, props.good))
const badPct = computed(() => `${(props.bad / max.value) * 100}%`)
const goodPct = computed(() => `${(props.good / max.value) * 100}%`)
const ratio = computed(() => {
  const r = props.lowerIsBetter ? props.bad / props.good : props.good / props.bad
  return `${r >= 10 ? r.toFixed(1) : r.toFixed(2)}×`
})
</script>

<template>
  <figure class="bar-compare">
    <div class="bar-row">
      <span class="bar-name">{{ badLabel }}</span>
      <div class="bar-track"><div class="bar-fill tone-bad" :style="{ width: badPct }"></div></div>
      <span class="bar-value">{{ bad }}{{ unit }}</span>
    </div>
    <div class="bar-row">
      <span class="bar-name">{{ goodLabel }}</span>
      <div class="bar-track"><div class="bar-fill tone-good" :style="{ width: goodPct }"></div></div>
      <span class="bar-value">{{ good }}{{ unit }}</span>
    </div>
    <figcaption class="bar-caption">
      <strong>{{ ratio }}</strong> {{ lowerIsBetter ? 'bad ÷ good' : 'good ÷ bad' }}
      <span v-if="caption"> · {{ caption }}</span>
    </figcaption>
  </figure>
</template>
