<script setup lang="ts">
defineProps<{
  title?: string
  href?: string
  badge?: string
}>()
</script>

<template>
  <component :is="href ? 'a' : 'div'" :href="href" class="glass-card" :class="{ 'is-link': !!href }">
    <div v-if="$slots.icon || badge" class="glass-card-head">
      <span v-if="$slots.icon" class="glass-card-icon"><slot name="icon" /></span>
      <span v-if="badge" class="badge badge-info">{{ badge }}</span>
    </div>
    <h3 v-if="title" class="glass-card-title">{{ title }}</h3>
    <div class="glass-card-body"><slot /></div>
  </component>
</template>
