<script setup lang="ts">
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = defineProps<{ content: string }>()
const markdown = new MarkdownIt({ html: false, linkify: true, breaks: true })
markdown.renderer.rules.link_open = (tokens, index, options, _env, self) => {
  const token = tokens[index]
  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer')
  return self.renderToken(tokens, index, options)
}
const rendered = computed(() => DOMPurify.sanitize(markdown.render(props.content)))
</script>

<template>
  <div class="markdown" v-html="rendered"></div>
</template>

<style>
.markdown { font-size: 14px; line-height: 1.62; overflow-wrap: anywhere; }
.markdown > :first-child { margin-top: 0; }
.markdown > :last-child { margin-bottom: 0; }
.markdown p { margin: 0 0 0.8em; }
.markdown h1, .markdown h2, .markdown h3 { line-height: 1.35; margin: 1.2em 0 0.55em; }
.markdown h1 { font-size: 1.3em; } .markdown h2 { font-size: 1.16em; } .markdown h3 { font-size: 1.05em; }
.markdown ul, .markdown ol { padding-left: 1.35em; margin: 0.55em 0 0.9em; }
.markdown li + li { margin-top: 0.25em; }
.markdown code { border: 1px solid #d8ddd9; background: #edf0ed; border-radius: 5px; padding: 0.1em 0.35em; font: 0.88em/1.5 'SFMono-Regular', Consolas, monospace; }
.markdown pre { overflow-x: auto; border: 1px solid #303735; background: #202523; color: #eef4f0; border-radius: 12px; padding: 14px 16px; margin: 0.9em 0; }
.markdown pre code { border: 0; background: transparent; padding: 0; color: inherit; }
.markdown blockquote { border-left: 3px solid #8c6a3c; color: #5f6661; margin: 0.8em 0; padding-left: 1em; }
.markdown table { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0.9em 0; }
.markdown th, .markdown td { border: 1px solid #d6dad6; padding: 7px 10px; text-align: left; white-space: nowrap; }
.markdown th { background: #eef0ec; }
.markdown a { color: #306e58; text-decoration-thickness: 1px; text-underline-offset: 3px; }
</style>
