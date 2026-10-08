<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'tip' | 'warning' | 'danger' | 'info'
    title?: string
  }>(),
  { type: 'info', title: undefined },
)

const defaults: Record<string, string> = {
  tip: 'Tip',
  warning: 'Warning',
  danger: 'Danger',
  info: 'Note',
}

const heading = computed(() => props.title ?? defaults[props.type])
</script>

<template>
  <aside class="site-callout" :class="`callout-${type}`" role="note">
    <p class="callout-title">{{ heading }}</p>
    <div class="callout-body"><slot /></div>
  </aside>
</template>
