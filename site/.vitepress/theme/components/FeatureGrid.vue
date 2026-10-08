<script setup lang="ts">
defineProps<{ cols?: 1 | 2 | 3 | 5 }>()
</script>

<template>
  <div class="feature-grid" :class="`cols-${cols ?? 3}`">
    <slot />
  </div>
</template>
