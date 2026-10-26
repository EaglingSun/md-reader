// Vditor + QWebChannel bridge.
// Python(Bridge)에서 시그널이 오면 Vditor를 갱신하고,
// Vditor 변경 이벤트는 bridge.onChange로 Python에 전달한다.

let vditor = null;
let bridge = null;
let currentMode = "ir";        // ir | wysiwyg | sv
let currentTheme = "classic";  // classic | dark
let pendingContent = "";

const VDITOR_CDN = "https://cdn.jsdelivr.net/npm/vditor@3.10.9";

// Vditor는 본문 폭을 preview.maxWidth(기본 800px)로 묶고 남는 폭을 좌우 여백으로 쓴다.
// 상한을 사실상 없애 본문이 창 폭을 따라가게 한다 (여백은 Vditor 최소값 35px).
const CONTENT_MAX_WIDTH = 100000;

function buildOptions(mode, theme, initialValue) {
  const isDark = theme === "dark";
  return {
    mode: mode,
    theme: isDark ? "dark" : "classic",
    lang: "ko_KR",        // Vditor default is zh_CN - force Korean tooltips/menus
    cdn: VDITOR_CDN,
    height: "100%",
    width: "100%",
    value: initialValue || "",
    cache: { enable: false },
    toolbar: [
      "emoji", "headings", "bold", "italic", "strike", "|",
      "line", "quote", "list", "ordered-list", "check", "outdent", "indent", "|",
      "code", "inline-code", "insert-after", "insert-before", "|",
      "table", "link", "|",
      "undo", "redo", "|",
      "edit-mode", "preview", "outline",
    ],
    preview: {
      maxWidth: CONTENT_MAX_WIDTH,
      theme: { current: isDark ? "dark" : "light" },
      hljs: { enable: true, lineNumber: true, style: isDark ? "github-dark" : "github" },
      markdown: {
        autoSpace: true,
        mark: true,
        footnotes: true,
        linkBase: "",
      },
      math: { engine: "KaTeX" },
    },
    counter: { enable: true, type: "text" },
    input: (md) => {
      if (bridge) bridge.onChange(md);
    },
    after: () => {
      if (pendingContent) {
        vditor.setValue(pendingContent);
        pendingContent = "";
      }
      // mermaid/code 등 렌더 트리거
      Vditor.mermaidRender(document.getElementById("vditor"), VDITOR_CDN, currentTheme);
      Vditor.codeRender(document.getElementById("vditor"));
      if (bridge && bridge.onEditorReady) {
        bridge.onEditorReady();
      }
    },
  };
}

function initVditor(mode, theme, initialValue) {
  const container = document.getElementById("vditor");
  container.innerHTML = "";
  vditor = new Vditor("vditor", buildOptions(mode, theme, initialValue));
}

function reinitWith(newMode, newTheme) {
  const value = vditor ? vditor.getValue() : "";
  currentMode = newMode || currentMode;
  currentTheme = newTheme || currentTheme;
  document.body.classList.toggle("dark", currentTheme === "dark");
  initVditor(currentMode, currentTheme, value);
}

function exportHtml() {
  if (!vditor || !bridge) return;
  // getHTML 비동기 (Promise) — 안전하게 await
  const result = vditor.getHTML();
  if (result && typeof result.then === "function") {
    result.then((html) => bridge.onHTMLReady(html));
  } else {
    bridge.onHTMLReady(result || "");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  // QWebChannel 초기화. qt.webChannelTransport는 Python 측에서 주입.
  new QWebChannel(qt.webChannelTransport, function (channel) {
    bridge = channel.objects.bridge;

    bridge.loadContent.connect(function (md) {
      // Detect "document is exactly a single code fence" (YAML/JSON case).
      // When true, body.code-only enables CSS that drops the code block's
      // internal max-height so the outer editor scroll handles long content.
      const codeOnly = /^\s*(`{3,})(yaml|yml|json|text)\s*\n[\s\S]*\n\1\s*$/.test(md);
      document.body.classList.toggle("code-only", codeOnly);
      if (vditor) {
        vditor.setValue(md);
      } else {
        pendingContent = md;
      }
    });

    bridge.themeChanged.connect(function (theme) {
      reinitWith(null, theme);
    });

    bridge.modeChanged.connect(function (mode) {
      reinitWith(mode, null);
    });

    bridge.requestExportHTML.connect(function () {
      exportHtml();
    });

    // 초기 Vditor 부팅
    initVditor(currentMode, currentTheme, "");
  });
});
