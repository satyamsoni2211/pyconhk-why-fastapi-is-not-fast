import { h } from 'vue'
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import './style.css'

import GlassCard from './components/GlassCard.vue'
import FeatureGrid from './components/FeatureGrid.vue'
import StatCard from './components/StatCard.vue'
import StatGrid from './components/StatGrid.vue'
import Callout from './components/Callout.vue'
import BadGood from './components/BadGood.vue'
import Timeline from './components/Timeline.vue'
import BarCompare from './components/BarCompare.vue'
import Checklist from './components/Checklist.vue'
import ChecklistItem from './components/ChecklistItem.vue'
import CopyCommand from './components/CopyCommand.vue'
import EnvBadge from './components/EnvBadge.vue'
import ThemeAurora from './components/ThemeAurora.vue'

const theme: Theme = {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => h(ThemeAurora),
    })
  },
  enhanceApp({ app }) {
    app.component('GlassCard', GlassCard)
    app.component('FeatureGrid', FeatureGrid)
    app.component('StatCard', StatCard)
    app.component('StatGrid', StatGrid)
    app.component('Callout', Callout)
    app.component('BadGood', BadGood)
    app.component('Timeline', Timeline)
    app.component('BarCompare', BarCompare)
    app.component('Checklist', Checklist)
    app.component('ChecklistItem', ChecklistItem)
    app.component('CopyCommand', CopyCommand)
    app.component('EnvBadge', EnvBadge)
  },
}

export default theme
