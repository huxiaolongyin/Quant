<template>
  <div class="monaco-editor-container" ref="containerRef">
    <vue-monaco-editor
      v-model:value="codeValue"
      language="python"
      :theme="editorTheme"
      :options="editorOptions"
      @mount="handleMount"
      @change="handleChange"
    />
  </div>
</template>

<script setup lang="ts">
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { computed, ref, shallowRef } from 'vue'
import type { editor } from 'monaco-editor'

interface Props {
  modelValue: string
  readOnly?: boolean
  minimap?: boolean
  fontSize?: number
  lineNumbers?: 'on' | 'off' | 'relative'
  wordWrap?: 'on' | 'off'
  tabSize?: number
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
  (e: 'cursorChange', position: { lineNumber: number; column: number }): void
  (e: 'ready', editor: editor.IStandaloneCodeEditor): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  readOnly: false,
  minimap: false,
  fontSize: 14,
  lineNumbers: 'on',
  wordWrap: 'on',
  tabSize: 4
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement>()
const editorInstance = shallowRef<editor.IStandaloneCodeEditor>()
const monacoInstance = shallowRef<typeof import('monaco-editor')>()

const codeValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const editorTheme = computed(() => 'vs-dark')

const editorOptions = computed<editor.IStandaloneEditorConstructionOptions>(() => ({
  readOnly: props.readOnly,
  minimap: { enabled: props.minimap },
  fontSize: props.fontSize,
  lineNumbers: props.lineNumbers,
  wordWrap: props.wordWrap,
  tabSize: props.tabSize,
  automaticLayout: true,
  scrollBeyondLastLine: false,
  renderLineHighlight: 'all',
  cursorBlinking: 'smooth',
  cursorSmoothCaretAnimation: 'on',
  smoothScrolling: true,
  padding: { top: 16, bottom: 16 },
  folding: true,
  foldingHighlight: true,
  showFoldingControls: 'mouseover',
  bracketPairColorization: { enabled: true },
  guides: {
    bracketPairs: true,
    indentation: true
  },
  suggest: {
    showKeywords: true,
    showSnippets: true
  },
  quickSuggestions: {
    other: true,
    comments: false,
    strings: false
  },
  acceptSuggestionOnCommitCharacter: true,
  formatOnPaste: true,
  formatOnType: true
}))

const handleMount = (
  editor: editor.IStandaloneCodeEditor,
  monaco: typeof import('monaco-editor')
) => {
  editorInstance.value = editor
  monacoInstance.value = monaco

  editor.onDidChangeCursorPosition((e) => {
    emit('cursorChange', {
      lineNumber: e.position.lineNumber,
      column: e.position.column
    })
  })

  emit('ready', editor)
}

const handleChange = (value: string | undefined) => {
  emit('change', value || '')
}

const setMarkers = (errors: { line: number; message: string; severity: 'error' | 'warning' }[]) => {
  if (!monacoInstance.value) return

  const markers = errors.map((err) => ({
    startLineNumber: err.line,
    startColumn: 1,
    endLineNumber: err.line,
    endColumn: 1000,
    message: err.message,
    severity: err.severity === 'error' 
      ? monacoInstance.value!.MarkerSeverity.Error 
      : monacoInstance.value!.MarkerSeverity.Warning
  }))

  monacoInstance.value.editor.setModelMarkers(
    editorInstance.value?.getModel()!,
    'python',
    markers
  )
}

const clearMarkers = () => {
  if (!monacoInstance.value) return
  monacoInstance.value.editor.setModelMarkers(
    editorInstance.value?.getModel()!,
    'python',
    []
  )
}

const focus = () => {
  editorInstance.value?.focus()
}

const getLineCount = () => {
  return editorInstance.value?.getModel()?.getLineCount() || 0
}

defineExpose({
  setMarkers,
  clearMarkers,
  focus,
  getLineCount,
  getEditor: () => editorInstance.value,
  getMonaco: () => monacoInstance.value
})
</script>

<style scoped>
.monaco-editor-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.monaco-editor-container :deep(.monaco-editor) {
  padding-top: 0;
}

.monaco-editor-container :deep(.monaco-editor .margin) {
  background-color: #0d1117;
}

.monaco-editor-container :deep(.monaco-editor .monaco-editor-background) {
  background-color: #0d1117;
}
</style>