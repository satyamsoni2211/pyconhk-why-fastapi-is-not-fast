<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

const props = defineProps<{ id: string }>()
const checked = ref(false)
const KEY_PREFIX = 'fastapi-workshop:checklist:'

// Persisted per viewer in localStorage. Every access is guarded so the page
// renders correctly in SSR, private windows, or with storage blocked.
onMounted(() => {
  try {
    checked.value = window.localStorage.getItem(KEY_PREFIX + props.id) === '1'
  } catch {
    checked.value = false
  }
})

watch(checked, (v) => {
  try {
    window.localStorage.setItem(KEY_PREFIX + props.id, v ? '1' : '0')
  } catch {
    /* storage unavailable: keep in-memory state only */
  }
})
</script>

<template>
  <li class="checklist-item" :class="{ done: checked }">
    <label>
      <input type="checkbox" v-model="checked" :aria-label="`Mark done: ${id}`" />
      <span class="checklist-text"><slot /></span>
    </label>
  </li>
</template>
