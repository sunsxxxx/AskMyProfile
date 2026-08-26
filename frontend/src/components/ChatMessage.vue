<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ChatMessage } from '../types/chat'
import MarkdownContent from './MarkdownContent.vue'

const props = defineProps<{ message: ChatMessage; streaming?: boolean }>()
const intermediateExpanded = ref(!props.message.content)
let answerStarted = Boolean(props.message.content)

const intermediateLines = computed(() => {
  if (!props.message.intermediate) return []

  return props.message.intermediate
    .split(/\n+/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('收到问题：'))
    .map((line) => {
      if (/正在调用技能资料检索工具(?:\s+search_skill)?。?/.test(line)) return '正在检索技术栈资料…'
      if (/正在调用项目资料检索工具(?:\s+search_project)?。?/.test(line)) return '正在检索相关项目经历…'
      if (/正在调用简历资料检索工具(?:\s+search_resume)?。?/.test(line)) return '正在检索简历与经历资料…'
      if (/正在调用GitHub 公开仓库检索工具(?:\s+search_github)?。?/.test(line)) return '正在检索 GitHub 项目资料…'
      if (line === '技能资料检索完成。') return '技术栈资料检索完成'
      if (line === '项目资料检索完成。') return '项目经历检索完成'
      if (line === '简历资料检索完成。') return '简历与经历资料检索完成'
      if (line === 'GitHub 公开仓库检索完成。') return 'GitHub 项目资料检索完成'
      if (line === 'Agent 判断该问题无需检索个人资料。') return '已确认无需检索额外资料'
      if (line === '正在生成最终回答。') return '正在组织回答…'
      return line
        .replace(/\s+(search_(?:resume|project|skill|github))(?=[。,.，]|$)/g, '')
        .replace('正在调用', '正在使用')
        .replace('工具。', '。')
    })
})

const intermediateContent = computed(() => intermediateLines.value.join('\n\n'))
const completedLabel = computed(() => {
  const trace = props.message.intermediate ?? ''
  const hasSkill = trace.includes('技能资料检索') || trace.includes('search_skill')
  const hasProject = trace.includes('项目资料检索') || trace.includes('search_project')
  if (hasSkill && hasProject) return '已检索技术栈与项目经历'
  if (hasSkill) return '已检索技术栈资料'
  if (hasProject) return '已检索相关项目经历'
  if (trace.includes('GitHub') || trace.includes('search_github')) return '已检索 GitHub 项目资料'
  if (trace.includes('简历') || trace.includes('search_resume')) return '已检索简历与经历资料'
  return '分析完成'
})

watch(
  () => props.message.content,
  (content) => {
    if (content && !answerStarted) {
      answerStarted = true
      intermediateExpanded.value = false
    }
  },
)
</script>
<template>
  <article class="message" :class="[`message--${message.role}`, { 'message--error': message.error }]">
    <div v-if="message.role === 'assistant'" class="avatar" aria-hidden="true"><span class="avatar__image"><img src="/ai-avatar.png" alt="" /></span></div>
    <div class="message__body">
      <div v-if="intermediateContent" class="intermediate" :class="{ 'intermediate--collapsed': !intermediateExpanded }" aria-label="处理过程">
        <button
          type="button"
          class="intermediate__toggle"
          :aria-expanded="intermediateExpanded"
          @click="intermediateExpanded = !intermediateExpanded"
        >
          <span class="intermediate__label">
            <span class="intermediate__state" aria-hidden="true">{{ message.content ? '✓' : '✦' }}</span>
            {{ message.content ? completedLabel : '处理过程' }}
          </span>
          <svg class="intermediate__indicator" :class="{ 'intermediate__indicator--expanded': intermediateExpanded }" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 4 4 4-4 4" /></svg>
        </button>
        <div class="intermediate__reveal" :class="{ 'intermediate__reveal--expanded': intermediateExpanded }" :aria-hidden="!intermediateExpanded">
          <div class="intermediate__content">
            <MarkdownContent :content="intermediateContent" /><span v-if="streaming && !message.content" class="cursor cursor--muted" aria-hidden="true"></span>
          </div>
        </div>
      </div>
      <div v-if="message.content" class="bubble"><MarkdownContent :content="message.content" /><span v-if="streaming" class="cursor" aria-hidden="true"></span></div>
      <details v-if="message.sources?.length" class="sources">
        <summary><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 4 4 4-4 4" /></svg><span>参考资料&nbsp; · &nbsp;{{ message.sources.length }}</span></summary>
        <ul><li v-for="source in message.sources" :key="`${source.source}:${source.section}`"><span>{{ source.title }}</span><small>{{ source.section || source.source }}</small></li></ul>
      </details>
    </div>
  </article>
</template>
<style scoped>
.message { width: min(100%, 1080px); margin: 0 auto; display: flex; align-items: flex-start; gap: 13px; padding: 13px 22px; }
.message--user { justify-content: flex-end; padding-top: 8px; padding-bottom: 8px; padding-left: 34%; }
.message--assistant + .message--user { margin-top: 22px; }
.message__body { min-width: 0; width: min(74%, 760px); }
.message--user .message__body { width: auto; max-width: min(66%, 620px); }
.avatar { width: 34px; height: 34px; flex: 0 0 auto; display: grid; place-items: center; margin-top: 1px; }
.avatar__image { width: 34px; height: 34px; display: block; }
.avatar__image img { width: 100%; height: 100%; display: block; object-fit: contain; }
.bubble { color: #30323a; }
.message--assistant .bubble { padding: 0 2px; border: 0; background: transparent; }
.message--user .bubble { padding: 11px 16px; border: 1px solid rgba(216,226,240,.82); border-radius: 18px 18px 5px 18px; background: #f0f5fb; color: #292d35; }
.message--error .bubble { color: #862d2d; }
.cursor { display: inline-block; width: 5px; height: 16px; margin-left: 3px; vertical-align: -3px; border-radius: 2px; background: #69768a; animation: blink 1s step-end infinite; }
.intermediate { margin: 0 0 12px; padding: 9px 11px; border-radius: 10px; background: rgba(246,247,249,.8); color: #7f8691; font-size: 12px; line-height: 1.5; transition: padding .2s ease, background .2s ease; }
.intermediate--collapsed { padding: 2px 1px; background: transparent; }
.intermediate__toggle { width: fit-content; min-height: 22px; padding: 0; border: 0; background: transparent; color: inherit; display: flex; align-items: center; justify-content: flex-start; gap: 6px; cursor: pointer; text-align: left; }
.intermediate__toggle:hover { color: #5f6671; }
.intermediate__label { display: flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 500; }
.intermediate__state { width: 14px; color: #9aa1ab; text-align: center; }
.intermediate__indicator { width: 15px; height: 15px; flex: 0 0 auto; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; transition: transform .2s ease; }
.intermediate__indicator--expanded { transform: rotate(90deg); }
.intermediate__reveal { display: grid; grid-template-rows: 0fr; opacity: 0; transition: grid-template-rows .2s ease, opacity .18s ease; }
.intermediate__reveal--expanded { grid-template-rows: 1fr; opacity: 1; }
.intermediate__content { min-height: 0; overflow: hidden; }
.intermediate__content :deep(.markdown) { padding: 5px 3px 1px 21px; color: #858c97; font-size: 12px; line-height: 1.5; }
.intermediate__content :deep(.markdown p) { position: relative; margin: 0 0 3px; }
.intermediate__content :deep(.markdown p)::before { content: ''; position: absolute; top: .68em; left: -13px; width: 3px; height: 3px; border-radius: 50%; background: #bdc2ca; }
.cursor--muted { height: 12px; background: #a5abb4; }
.sources { margin-top: 18px; color: #8a909c; font-size: 13px; }
.sources summary { width: fit-content; display: flex; align-items: center; gap: 5px; padding: 3px 1px; border-radius: 4px; cursor: pointer; user-select: none; list-style: none; transition: color .18s ease; }
.sources summary::-webkit-details-marker { display: none; }
.sources summary:hover { color: #555d69; }
.sources summary svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; transition: transform .18s ease; }
.sources[open] summary svg { transform: rotate(90deg); }
.sources ul { list-style: none; padding: 7px 0 0 20px; margin: 0; display: grid; gap: 0; }
.sources li { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: baseline; gap: 18px; padding: 7px 4px; border-bottom: 1px solid rgba(229,232,237,.72); }
.sources li:last-child { border-bottom: 0; }
.sources li span { overflow: hidden; color: #5b626e; font-size: 12px; font-weight: 500; text-overflow: ellipsis; white-space: nowrap; }
.sources small { min-width: 8em; color: #9aa0aa; font-size: 11px; text-align: right; white-space: normal; overflow-wrap: anywhere; }
@keyframes blink { 50% { opacity: 0; } }
@media (max-width: 1024px) {
  .message { padding-right: 14px; padding-left: 14px; }
  .message__body { width: min(75%, 730px); }
  .message--user .message__body { max-width: 72%; }
}
@media (max-width: 720px) {
  .message { gap: 9px; padding: 11px 3px; }
  .message--user { padding: 7px 3px 7px 15%; }
  .message__body { width: calc(100% - 41px); max-width: none; }
  .message--user .message__body { max-width: 85%; }
  .avatar { width: 32px; height: 32px; }
  .avatar__image { width: 32px; height: 32px; }
  .message--user .bubble { padding: 10px 14px; }
  .intermediate { margin-bottom: 10px; }
  .sources li { grid-template-columns: minmax(0, 1fr); gap: 2px; }
  .sources small { min-width: 0; text-align: left; }
}
</style>
