<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ChatMessage } from '../types/chat'
import MarkdownContent from './MarkdownContent.vue'

const props = defineProps<{ message: ChatMessage; streaming?: boolean }>()
const intermediateExpanded = ref(!props.message.content)
let answerStarted = Boolean(props.message.content)

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
    <div v-if="message.role === 'assistant'" class="avatar" aria-hidden="true"><span class="avatar__image"><img src="/spark-mark.svg" alt="" /></span></div>
    <div class="message__body">
      <div v-if="message.intermediate" class="intermediate" aria-label="处理中间状态">
        <button
          type="button"
          class="intermediate__toggle"
          :aria-expanded="intermediateExpanded"
          @click="intermediateExpanded = !intermediateExpanded"
        >
          <span class="intermediate__label">处理过程</span>
          <span
            class="intermediate__indicator"
            :class="{ 'intermediate__indicator--expanded': intermediateExpanded }"
            aria-hidden="true"
          >›</span>
        </button>
        <div v-show="intermediateExpanded" class="intermediate__content">
          <MarkdownContent :content="message.intermediate" /><span v-if="streaming && !message.content" class="cursor cursor--muted" aria-hidden="true"></span>
        </div>
      </div>
      <div v-if="message.content" class="bubble"><MarkdownContent :content="message.content" /><span v-if="streaming" class="cursor" aria-hidden="true"></span></div>
      <details v-if="message.sources?.length" class="sources"><summary>参考资料 · {{ message.sources.length }}</summary><ul><li v-for="source in message.sources" :key="`${source.source}:${source.section}`"><span>{{ source.title }}</span><small>{{ source.section || source.source }}</small></li></ul></details>
    </div>
  </article>
</template>
<style scoped>
.message { max-width: 1058px; margin: 0 auto; display: flex; align-items: flex-start; gap: 15px; padding: 10px 24px; }.message--user { justify-content: flex-end; padding-left: 31%; }.message__body { min-width: 0; max-width: 68%; }.avatar { width: 42px; height: 42px; flex: 0 0 auto; display: grid; place-items: center; border: 1px solid #e1e4e9; border-radius: 50%; background: #fff; box-shadow: 0 3px 10px rgba(34,43,58,.10); }.avatar__image { width: 23px; height: 23px; display: block; }.avatar__image img { width: 100%; height: 100%; display: block; object-fit: contain; }
.bubble { padding: 14px 17px; border: 1px solid #e1e4ea; border-radius: 15px; background: rgba(255,255,255,.72); color: #202226; box-shadow: 0 2px 7px rgba(45,55,75,.025); }.message--user .bubble { padding: 13px 18px; border-color: #e1e8f4; background: #edf3fd; }.message--error .bubble { color: #862d2d; }.cursor { display: inline-block; width: 6px; height: 16px; margin-left: 3px; vertical-align: -3px; border-radius: 2px; background: #586a86; animation: blink 1s step-end infinite; }
.intermediate { margin-bottom: 9px; padding: 10px 13px; border-left: 3px solid #c9ced6; border-radius: 8px; background: #f3f4f6; color: #7a808a; font-size: 12px; line-height: 1.55; }.intermediate__toggle { width: 100%; padding: 0; border: 0; background: transparent; color: inherit; display: flex; align-items: center; justify-content: space-between; cursor: pointer; text-align: left; }.intermediate__label { color: #969ca5; font-size: 10px; font-weight: 600; letter-spacing: .08em; }.intermediate__indicator { color: #969ca5; font-size: 17px; line-height: 1; transform: rotate(0deg); transition: transform .16s ease; }.intermediate__indicator--expanded { transform: rotate(90deg); }.intermediate__content { margin-top: 3px; }
.cursor--muted { height: 13px; background: #9aa0a9; }
.sources { margin-top: 9px; color: #697386; font-size: 11px; }.sources summary { padding: 5px 2px; cursor: pointer; user-select: none; }.sources ul { list-style: none; padding: 4px 0 0; margin: 0; display: grid; gap: 5px; }.sources li { display: flex; justify-content: space-between; gap: 14px; padding: 7px 9px; border-radius: 8px; background: #f5f7fa; }.sources li span { font-weight: 600; }.sources small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@keyframes blink { 50% { opacity: 0; } } @media (max-width: 720px) { .message { gap: 9px; padding: 9px 4px; }.message--user { padding-left: 16%; }.message__body { max-width: 84%; }.avatar { width: 36px; height: 36px; }.bubble { padding: 11px 13px; } }
</style>
