<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<template>
  <section class="checklist-card">
    <h3 v-if="title" class="checklist-title">{{ title }}</h3>
    <ul class="checklist">
      <slot />
    </ul>
  </section>
</template>
