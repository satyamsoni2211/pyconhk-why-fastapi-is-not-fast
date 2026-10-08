<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ cmd: string; label?: string }>()
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.cmd)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    copied.value = false
  }
}
</script>

<template>
  <div class="copy-command">
    <div class="copy-command-meta" v-if="label">{{ label }}</div>
    <div class="copy-command-row">
      <code class="copy-command-code"><span class="prompt" aria-hidden="true">$ </span>{{ cmd }}</code>
      <button type="button" class="copy-command-btn" @click="copy" :aria-label="`Copy command: ${cmd}`">
        {{ copied ? 'Copied' : 'Copy' }}
      </button>
    </div>
  </div>
</template>
