<script setup lang="ts"></script>

<template>
  <div class="bad-good">
    <section class="bad-good-panel panel-bad">
      <h3 class="bad-good-label"><span class="dot dot-bad" aria-hidden="true"></span>Bad</h3>
      <div class="bad-good-body"><slot name="bad" /></div>
    </section>
    <section class="bad-good-panel panel-good">
      <h3 class="bad-good-label"><span class="dot dot-good" aria-hidden="true"></span>Good</h3>
      <div class="bad-good-body"><slot name="good" /></div>
    </section>
  </div>
</template>
