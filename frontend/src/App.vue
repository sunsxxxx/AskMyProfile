<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import ChatMessage from './components/ChatMessage.vue'
import { useChat } from './composables/useChat'

const scrollArea = ref<HTMLElement | null>(null)
const inputArea = ref<HTMLTextAreaElement | null>(null)
const autoScrollEnabled = ref(true)

function scrollToBottom() {
  void nextTick(() => {
    if (!autoScrollEnabled.value || !scrollArea.value) return
    scrollArea.value.scrollTo({ top: scrollArea.value.scrollHeight, behavior: 'auto' })
  })
}

const { messages, input, status, isStreaming, canSend, send, stop, newConversation } = useChat(scrollToBottom)
const showStatus = computed(() => isStreaming.value && status.value && !messages.value.at(-1)?.intermediate)
const prompts = [
  { text: '介绍一下你做过的项目', icon: 'folder' },
  { text: '你 Redis 用得怎么样？', icon: 'database' },
  { text: '说说你的技术栈', icon: 'code' },
  { text: 'GitHub 上有哪些项目？', icon: 'github' },
]

async function submit(preset?: string) {
  autoScrollEnabled.value = true
  await send(preset)
}

function onScroll() {
  if (!scrollArea.value) return
  const distanceFromBottom = scrollArea.value.scrollHeight - scrollArea.value.scrollTop - scrollArea.value.clientHeight
  autoScrollEnabled.value = distanceFromBottom < 96
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    void submit()
  }
}

function resetConversation() {
  autoScrollEnabled.value = true
  newConversation()
  void nextTick(() => inputArea.value?.focus())
}
</script>

<template>
  <main class="shell" :class="{ 'shell--chat': messages.length > 0 }">
    <div class="stage">
      <header v-if="messages.length" class="chat-toolbar">
        <button class="new-button" type="button" :disabled="isStreaming" @click="resetConversation">
          <span aria-hidden="true">＋</span> 新对话
        </button>
      </header>

      <section ref="scrollArea" class="conversation" aria-live="polite" @scroll="onScroll">
        <div v-if="messages.length === 0" class="welcome-card">
          <div class="welcome__eyebrow">
            <span class="spark-image spark-image--eyebrow" aria-hidden="true"><img src="/spark-mark.svg" alt="" /></span>
            <span>个人知识助手</span>
          </div>
          <h1>你好，想了解我的哪一面？</h1>
          <p>这是一个基于真实项目经历与技术资料构建的 AI 助手。你可以询问我的技术栈、项目经历、实习经历或 GitHub 项目。</p>

          <div class="prompt-grid">
            <button v-for="prompt in prompts" :key="prompt.text" type="button" @click="submit(prompt.text)">
              <span class="prompt-icon" aria-hidden="true">
                <svg v-if="prompt.icon === 'folder'" viewBox="0 0 24 24"><path d="M3.5 6.8h6l1.7 2h9.3v9.7a2 2 0 0 1-2 2h-15v-13.7Z"/><path d="M3.5 7V5.5a2 2 0 0 1 2-2h3l1.7 2h3"/></svg>
                <svg v-else-if="prompt.icon === 'database'" viewBox="0 0 24 24"><ellipse cx="12" cy="5.5" rx="7.5" ry="3"/><path d="M4.5 5.5v6c0 1.65 3.36 3 7.5 3s7.5-1.35 7.5-3v-6M4.5 11.5v6c0 1.65 3.36 3 7.5 3s7.5-1.35 7.5-3v-6"/></svg>
                <svg v-else-if="prompt.icon === 'code'" viewBox="0 0 24 24"><path d="m8.5 6-5 6 5 6M15.5 6l5 6-5 6M14 3l-4 18"/></svg>
                <svg v-else viewBox="0 0 24 24"><path d="M12 2.8a9.2 9.2 0 0 0-2.9 17.93c.46.09.63-.2.63-.44v-1.77c-2.57.56-3.11-1.09-3.11-1.09-.42-1.07-1.03-1.35-1.03-1.35-.84-.57.06-.56.06-.56.93.07 1.42.96 1.42.96.83 1.42 2.17 1.01 2.7.77.08-.6.32-1.01.59-1.24-2.05-.23-4.21-1.03-4.21-4.57 0-1.01.36-1.84.95-2.48-.1-.23-.41-1.17.09-2.45 0 0 .78-.25 2.53.95A8.8 8.8 0 0 1 12 7.15c.78 0 1.55.1 2.28.31 1.76-1.2 2.53-.95 2.53-.95.5 1.28.19 2.22.09 2.45.59.64.95 1.47.95 2.48 0 3.55-2.16 4.33-4.22 4.56.33.29.63.85.63 1.72v2.57c0 .25.17.54.64.44A9.2 9.2 0 0 0 12 2.8Z" class="fill"/></svg>
              </span>
              <span class="prompt-text">{{ prompt.text }}</span>
              <span class="prompt-arrow" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12h13M14 7l5 5-5 5" /></svg></span>
            </button>
          </div>

          <div class="truth-note">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8 20 6v5.7c0 4.9-3.35 8.05-8 9.5-4.65-1.45-8-4.6-8-9.5V6l8-3.2Z"/><path d="m8.4 12 2.3 2.3 4.9-5"/></svg>
            仅根据已配置的个人资料回答经历类问题
          </div>
        </div>

        <div v-else class="message-list">
          <ChatMessage
            v-for="(message, index) in messages"
            :key="message.id"
            :message="message"
            :streaming="isStreaming && index === messages.length - 1 && message.role === 'assistant'"
          />
          <div v-if="showStatus" class="status"><i></i><i></i><i></i>{{ status }}</div>
        </div>
      </section>

      <footer class="composer-wrap">
        <div class="composer" :class="{ 'composer--active': input.trim() }">
          <span v-if="messages.length === 0" class="composer-spark" aria-hidden="true">
            <span class="spark-image"><img src="/spark-mark.svg" alt="" /></span>
          </span>
          <textarea ref="inputArea" v-model="input" maxlength="2000" rows="1" :disabled="isStreaming" aria-label="向个人知识助手提问" placeholder="询问项目、经历或技术栈…" @keydown="onKeydown"></textarea>
          <button v-if="isStreaming" class="send-button stop-button" type="button" aria-label="停止生成" @click="stop"><span></span></button>
          <button v-else class="send-button" type="button" :disabled="!canSend" aria-label="发送" @click="submit()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M7 10l5-5 5 5" /></svg></button>
        </div>
        <p v-if="messages.length === 0">Enter 发送&nbsp;&nbsp;·&nbsp;&nbsp;Shift + Enter 换行&nbsp;&nbsp;·&nbsp;&nbsp;回答可能存在遗漏，请以正式简历为准</p>
      </footer>
    </div>
  </main>
</template>

<style>
:root { font-family: Inter, -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif; color: #202329; background: #f3f7ff; font-synthesis: none; }
* { box-sizing: border-box; }
html, body, #app { width: 100%; min-width: 320px; height: 100%; margin: 0; }
body { overflow: hidden; }
button, textarea { font: inherit; } button { color: inherit; }
.shell { height: 100%; height: 100dvh; padding: clamp(12px, 2.5dvh, 26px) clamp(12px, 2.5vw, 40px) clamp(10px, 2.3dvh, 24px); background: radial-gradient(circle at 56% 38%, rgba(255,255,255,.98) 0 13%, rgba(242,247,255,.84) 45%, rgba(229,237,251,.86) 76%, rgba(248,249,251,.96) 100%); }
.stage { width: min(1070px, 100%); height: 100%; margin: auto; display: grid; grid-template-rows: minmax(0, 1fr) auto; gap: 38px; }
.shell:not(.shell--chat) { overflow: hidden; }
.shell:not(.shell--chat) .stage { grid-template-rows: minmax(0, 1fr) auto; gap: clamp(10px, 3.3dvh, 32px); }
.conversation { min-height: 0; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; scrollbar-width: thin; scrollbar-color: #dfe3ea transparent; }
.conversation::-webkit-scrollbar { width: 6px; }
.conversation::-webkit-scrollbar-track { background: transparent; }
.conversation::-webkit-scrollbar-thumb { border-radius: 999px; background: #dfe3ea; }
.conversation::-webkit-scrollbar-thumb:hover { background: #c9ced7; }
.shell:not(.shell--chat) .conversation { display: flex; overflow: hidden; }
.welcome-card { width: 100%; max-height: min(590px, 100%); margin: auto 0; display: flex; flex-direction: column; justify-content: center; padding: clamp(18px, 4.9dvh, 46px) clamp(22px, 5.2vw, 64px) clamp(16px, 4.4dvh, 42px); border: 1px solid rgba(225,229,237,.7); border-radius: clamp(22px, 2vw, 32px); background: rgba(255,255,255,.8); box-shadow: 0 12px 40px rgba(64,89,134,.075); backdrop-filter: blur(18px); }
.welcome__eyebrow { width: fit-content; display: flex; align-items: center; gap: clamp(7px, 1vw, 10px); padding: clamp(7px, 1.05dvh, 10px) clamp(12px, 1.3vw, 17px); border-radius: 999px; background: #f7f8fb; font-size: clamp(12px, 1.6dvh, 15px); font-weight: 600; }
.spark-image { position: relative; width: 22px; height: 22px; display: block; overflow: hidden; }
.spark-image img { width: 100%; height: 100%; display: block; object-fit: contain; }
.spark-image--eyebrow { width: 18px; height: 18px; }
.welcome-card h1 { margin: clamp(16px, 3.6dvh, 34px) 0 clamp(8px, 1.6dvh, 15px); font-size: clamp(30px, min(3.3vw, 5.3dvh), 50px); line-height: 1.14; letter-spacing: -.045em; }
.welcome-card > p { margin: 0; color: #626977; font-size: clamp(13px, 1.75dvh, 16px); line-height: clamp(1.55em, 3.15dvh, 1.9em); }
.prompt-grid { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(8px, 1.7dvh, 16px) clamp(10px, 1.4vw, 18px); margin-top: clamp(14px, 3.6dvh, 34px); }
.prompt-grid button { min-height: clamp(60px, 9.6dvh, 90px); display: grid; grid-template-columns: clamp(38px, 4.7dvh, 44px) 1fr clamp(36px, 4.5dvh, 42px); align-items: center; gap: clamp(11px, 1.35vw, 17px); padding: clamp(8px, 1.3dvh, 12px) clamp(10px, 1.1vw, 14px) clamp(8px, 1.3dvh, 12px) clamp(12px, 1.6vw, 20px); border: 1px solid #dfe3eb; border-radius: clamp(14px, 1.3vw, 19px); background: rgba(255,255,255,.38); text-align: left; cursor: pointer; transition: border-color .18s, background .18s, transform .18s, box-shadow .18s; }
.prompt-grid button:hover { border-color: #bbc4d3; background: #fff; transform: translateY(-2px); box-shadow: 0 9px 24px rgba(61,79,113,.10); }
.prompt-icon { width: clamp(38px, 4.7dvh, 44px); height: clamp(38px, 4.7dvh, 44px); display: grid; place-items: center; border-radius: clamp(10px, 1vw, 13px); background: #050505; color: #fff; }
.prompt-icon svg { width: 23px; height: 23px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }.prompt-icon .fill { fill: currentColor; stroke: none; }
.prompt-text { font-size: clamp(13px, 1.75dvh, 16px); font-weight: 600; }.prompt-arrow { width: clamp(36px, 4.5dvh, 42px); height: clamp(36px, 4.5dvh, 42px); display: grid; place-items: center; border-radius: 50%; background: #f8f9fc; }
.prompt-arrow svg { width: 21px; height: 21px; fill: none; stroke: #17191d; stroke-width: 1.65; stroke-linecap: round; stroke-linejoin: round; }
.truth-note { display: flex; align-items: center; gap: 11px; margin-top: clamp(12px, 3.6dvh, 34px); color: #707786; font-size: clamp(11px, 1.45dvh, 13px); }.truth-note svg { width: clamp(17px, 2.1dvh, 20px); height: clamp(17px, 2.1dvh, 20px); fill: none; stroke: #687485; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.composer-wrap { position: relative; }.composer { min-height: clamp(56px, 7.6dvh, 70px); display: flex; align-items: center; gap: 12px; border: 1px solid #e2e6ed; border-radius: 999px; padding: 6px 10px 6px 19px; background: rgba(255,255,255,.94); box-shadow: 0 5px 18px rgba(45,71,118,.055); transition: border-color .18s, box-shadow .18s; }
.composer:focus-within { border-color: #c7cfda; box-shadow: 0 0 0 3px rgba(105,128,169,.055), 0 6px 20px rgba(45,71,118,.065); }
.composer-spark { width: 42px; height: 42px; flex: 0 0 auto; display: grid; place-items: center; border-radius: 50%; background: #f8f9fc; }
.composer textarea { width: 100%; min-height: 34px; max-height: 120px; resize: none; border: 0; outline: 0; padding: 7px 0 3px; color: #202226; background: transparent; font-size: 16px; line-height: 1.5; }.composer textarea::placeholder { color: #8f96a3; }
.send-button { width: 44px; height: 44px; flex: 0 0 auto; display: grid; place-items: center; border: 0; border-radius: 50%; background: #0b0b0c; color: #fff; cursor: pointer; transition: transform .18s, opacity .18s; }.send-button svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }.send-button:hover:not(:disabled) { transform: translateY(-1px); }.send-button:disabled { opacity: 1; cursor: not-allowed; }
.stop-button { display: grid; place-items: center; }.stop-button span { width: 11px; height: 11px; border-radius: 2px; background: #fff; }.composer-wrap > p { margin: clamp(5px, 1.4dvh, 13px) auto 0; color: #727a89; font-size: clamp(10px, 1.3dvh, 12px); text-align: center; }
.shell--chat { padding: clamp(16px, 2.3vh, 24px) 24px; }.shell--chat .stage { position: relative; grid-template-rows: 58px minmax(0, 1fr) auto; gap: 0; width: min(1220px, 100%); border: 1px solid rgba(224,228,235,.72); border-radius: 24px; padding: 0 28px 18px; background: rgba(255,255,255,.79); box-shadow: 0 12px 40px rgba(64,89,134,.07); backdrop-filter: blur(18px); overflow: hidden; }
.chat-toolbar { display: flex; justify-content: flex-end; align-items: center; }.new-button { display: flex; align-items: center; gap: 6px; border: 1px solid #e5e8ed; border-radius: 11px; padding: 8px 12px; background: rgba(255,255,255,.72); color: #4c525c; font-size: 12px; cursor: pointer; transition: color .18s, border-color .18s, background .18s; }.new-button:hover:not(:disabled) { border-color: #cbd1da; background: rgba(255,255,255,.96); color: #23262b; }.new-button:disabled { opacity: .45; cursor: not-allowed; }
.message-list { padding: 1px 0 36px; }.status { width: min(100%, 1080px); margin: 0 auto; padding: 5px 22px 13px 69px; display: flex; align-items: center; gap: 4px; color: #8a909c; font-size: 12px; }.status i { width: 3px; height: 3px; border-radius: 50%; background: #9299a5; animation: pulse 1.2s infinite; }.status i:nth-child(2) { animation-delay: .15s; }.status i:nth-child(3) { margin-right: 5px; animation-delay: .3s; }
.shell--chat .composer-wrap { width: min(920px, calc(100% - 44px)); margin: 0 auto; }
.shell--chat .composer { min-height: 52px; padding: 5px 7px 5px 19px; border-radius: 999px; }.shell--chat .composer textarea { font-size: 14px; }.shell--chat .send-button { width: 39px; height: 39px; }
@keyframes pulse { 0%, 70%, 100% { opacity: .25; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-2px); } }
@media (max-height: 540px) and (min-width: 721px) { .shell:not(.shell--chat) { height: auto; min-height: 100dvh; overflow-y: auto; }.shell:not(.shell--chat) .stage { min-height: 520px; } }
@media (max-width: 1024px) and (min-width: 721px) { .shell--chat .stage { padding-right: 20px; padding-left: 20px; }.shell--chat .composer-wrap { width: min(880px, calc(100% - 28px)); } }
@media (max-width: 720px) { .shell { padding: 16px 12px 12px; }.stage { gap: 14px; }.welcome-card { min-height: 0; justify-content: flex-start; padding: 28px 20px 24px; border-radius: 24px; }.welcome__eyebrow { padding: 8px 13px; font-size: 13px; }.welcome-card h1 { margin-top: 24px; font-size: 32px; }.welcome-card > p { font-size: 14px; line-height: 1.75; }.desktop-break { display: none; }.prompt-grid { grid-template-columns: 1fr; gap: 9px; margin-top: 24px; }.prompt-grid button { min-height: 61px; grid-template-columns: 38px 1fr 34px; gap: 12px; padding: 9px 10px 9px 12px; border-radius: 15px; }.prompt-icon { width: 38px; height: 38px; border-radius: 11px; }.prompt-icon svg { width: 20px; height: 20px; }.prompt-text { font-size: 14px; }.prompt-arrow { width: 34px; height: 34px; font-size: 21px; }.truth-note { margin-top: 22px; font-size: 11px; }.composer { min-height: 56px; padding: 6px 8px 6px 13px; }.composer-spark { width: 36px; height: 36px; }.send-button { width: 42px; height: 42px; }.composer-wrap > p { display: none; }.shell--chat { padding: 0; }.shell--chat .stage { width: 100%; grid-template-rows: 54px minmax(0, 1fr) auto; border: 0; border-radius: 0; padding: 0 10px 10px; }.shell--chat .composer-wrap { width: 100%; }.shell--chat .composer { min-height: 50px; padding-left: 15px; } }
@media (max-width: 720px) { .shell:not(.shell--chat) { height: auto; min-height: 100dvh; overflow-y: auto; }.shell:not(.shell--chat) .stage { height: auto; min-height: calc(100dvh - 28px); grid-template-rows: minmax(0, 1fr) auto; }.shell:not(.shell--chat) .conversation { overflow: visible; }.shell:not(.shell--chat) .welcome-card { max-height: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; transition-duration: .01ms !important; } }
</style>
