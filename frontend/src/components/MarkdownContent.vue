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
.markdown { font-size: 15px; line-height: 1.72; overflow-wrap: anywhere; }
.markdown > :first-child { margin-top: 0; }
.markdown > :last-child { margin-bottom: 0; }
.markdown p { margin: 0 0 0.9em; }
.markdown h1, .markdown h2, .markdown h3 { color: #24272e; font-weight: 600; line-height: 1.4; margin: 1.25em 0 0.58em; }
.markdown h1 { font-size: 1.3em; } .markdown h2 { font-size: 1.16em; } .markdown h3 { font-size: 1.05em; }
.markdown ul, .markdown ol { padding-left: 1.4em; margin: 0.6em 0 1em; }
.markdown li + li { margin-top: 0.32em; }
.markdown strong { color: #282b32; font-weight: 600; }
.markdown code { border: 0; background: #f1f3f5; border-radius: 4px; padding: 0.08em 0.3em; color: #424750; font: 0.87em/1.5 'SFMono-Regular', Consolas, monospace; }
.markdown pre { overflow-x: auto; border: 1px solid #e6e8ec; background: #f7f8fa; color: #343840; border-radius: 10px; padding: 13px 15px; margin: 1em 0; }
.markdown pre code { border: 0; background: transparent; padding: 0; color: inherit; }
.markdown blockquote { border-left: 2px solid #c8ccd3; color: #646b76; margin: 0.9em 0; padding-left: 1em; }
.markdown table { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0.9em 0; }
.markdown th, .markdown td { border: 1px solid #e1e4e8; padding: 7px 10px; text-align: left; white-space: nowrap; }
.markdown th { background: #f5f6f8; }
.markdown a { color: #46698f; text-decoration-thickness: 1px; text-underline-offset: 3px; }
@media (max-width: 720px) { .markdown { font-size: 14.5px; line-height: 1.68; } }
</style>
