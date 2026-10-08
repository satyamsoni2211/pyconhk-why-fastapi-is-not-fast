<script setup lang="ts">
export interface TimelineRow {
  label: string
  start: number
  end: number
  tone?: 'good' | 'bad' | 'info' | 'warn'
}

const props = defineProps<{
  rows: TimelineRow[]
  total: number
  unit?: string
  caption?: string
}>()

function left(r: TimelineRow) {
  return `${(r.start / props.total) * 100}%`
}
function width(r: TimelineRow) {
  return `${((r.end - r.start) / props.total) * 100}%`
}
</script>

<template>
  <figure class="timeline">
    <div class="timeline-row" v-for="r in rows" :key="r.label">
      <div class="timeline-label">{{ r.label }}</div>
      <div class="timeline-track">
        <div
          class="timeline-bar"
          :class="`tone-${r.tone ?? 'info'}`"
          :style="{ left: left(r), width: width(r) }"
          :title="`${r.label}: ${r.start}–${r.end}${unit ?? 's'}`"
        ></div>
      </div>
    </div>
    <div class="timeline-axis" aria-hidden="true">
      <span>0</span>
      <span>{{ total }}{{ unit ?? 's' }}</span>
    </div>
    <figcaption v-if="caption" class="timeline-caption">{{ caption }}</figcaption>
  </figure>
</template>
