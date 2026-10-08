<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ env: 'postgres' | 'sqlite' }>()
const text = computed(() => (props.env === 'postgres' ? 'Postgres capture' : 'SQLite local'))
</script>

<template>
  <span class="badge env-badge" :class="`env-${env}`">{{ text }}</span>
</template>
