<script setup lang="ts">
defineProps<{
  value: string
  label: string
  sub?: string
  tone?: 'good' | 'bad' | 'neutral'
}>()
</script>

<template>
  <div class="stat-card" :class="`tone-${tone ?? 'neutral'}`">
    <div class="stat-value">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
    <div v-if="sub" class="stat-sub">{{ sub }}</div>
  </div>
</template>
