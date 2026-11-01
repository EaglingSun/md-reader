// Vditor + QWebChannel bridge.
// Python(Bridge)에서 시그널이 오면 Vditor를 갱신하고,
// Vditor 변경 이벤트는 bridge.onChange로 Python에 전달한다.

let vditor = null;
let bridge = null;
let currentMode = "ir";        // ir | wysiwyg | sv
let currentTheme = "classic";  // classic | dark
let pendingContent = "";
let readOnly = false;          // 코드 · 패치 파일 — Python 이 loadContent 로 알려 준다

// Vditor 를 다시 만들면(테마 · 모드 전환) contenteditable 이 되살아나므로 매번 다시 건다.
function applyReadOnly() {
  if (!vditor) return;
  if (readOnly) {
    vditor.disabled();
  } else {
    vditor.enable();
  }
  document.body.classList.toggle("read-only", readOnly);
}

// Vditor 가 lute · hljs · mermaid · katex · i18n 등을 `${cdn}/dist/...` 에서 불러온다.
// 설치본에 들어 있는 vendor/vditor 를 가리켜 인터넷 없이 그린다 (packaging/fetch_vditor.py).
const VDITOR_CDN = new URL("vendor/vditor", document.baseURI).href;

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
      applyReadOnly();
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

// PDF 내보내기용 줄 번호. Vditor 는 번호 열을 코드 글줄과 따로 그리고, 줄바꿈(pre-wrap)이면 화면에서 잰 줄 높이를
// px 로 박는다. 종이는 창보다 좁아 줄이 다르게 접히므로 그대로 인쇄하면 번호가 밀리고, 줄바꿈이 없는 마크다운
// 코드 블록은 긴 줄이 종이 오른쪽에서 잘린다. 인쇄 직전에 "줄마다 블록 하나 + 그 줄에 붙은 번호" 사본을 원본 옆에
// 넣어 인쇄 때만 보이게 하고(editor.css @media print), 끝나면 지운다. Python(editor.export_pdf)이 순서를 잡는다 —
// beforeprint 에서 바꾼 DOM 은 printToPdf 결과에 들어가지 않는다(2026-11-01 실측).
function splitCodeLines(code) {
  const lines = [];
  let line = document.createElement("span");
  let open = [];  // 지금 줄에서 열려 있는 hljs span 사본들 (줄이 바뀌면 같은 깊이로 다시 연다)
  const top = () => (open.length ? open[open.length - 1] : line);
  const newLine = () => {
    lines.push(line);
    line = document.createElement("span");
    const prev = open;
    open = [];
    let parent = line;
    for (const el of prev) {
      const c = el.cloneNode(false);
      parent.appendChild(c);
      open.push(c);
      parent = c;
    }
  };
  const walk = (node) => {
    for (const ch of node.childNodes) {
      if (ch.nodeType === Node.TEXT_NODE) {
        ch.textContent.split("\n").forEach((part, i) => {
          if (i > 0) newLine();
          if (part) top().appendChild(document.createTextNode(part));
        });
      } else if (ch.nodeType === Node.ELEMENT_NODE) {
        if (ch.classList.contains("vditor-linenumber__rows") || ch.classList.contains("vditor-linenumber__temp")) continue;
        const c = ch.cloneNode(false);
        top().appendChild(c);
        open.push(c);
        walk(ch);
        open.pop();
      }
    }
  };
  walk(code);
  lines.push(line);
  if (lines.length > 1 && lines[lines.length - 1].textContent === "") lines.pop();  // 끝 개행 (Vditor 와 같은 규칙)
  return lines;
}

function preparePrint() {
  finishPrint();
  let n = 0;
  document.querySelectorAll("#vditor code.vditor-linenumber").forEach((code) => {
    if (code.offsetParent === null) return;  // 접힌 원문 상자 등 안 보이는 것
    const copy = document.createElement("code");
    copy.className = code.className.replace(/\bvditor-linenumber\b/, "").trim() + " print-copy";
    for (const ln of splitCodeLines(code)) {
      ln.className = "print-line";
      copy.appendChild(ln);
    }
    code.classList.add("has-print-copy");
    code.insertAdjacentElement("afterend", copy);
    n += 1;
  });
  return n;
}

function finishPrint() {
  document.querySelectorAll("#vditor code.print-copy").forEach((c) => c.remove());
  document.querySelectorAll("#vditor code.has-print-copy").forEach((c) => c.classList.remove("has-print-copy"));
}

window.addEventListener("DOMContentLoaded", () => {
  // QWebChannel 초기화. qt.webChannelTransport는 Python 측에서 주입.
  new QWebChannel(qt.webChannelTransport, function (channel) {
    bridge = channel.objects.bridge;

    bridge.loadContent.connect(function (md, codeOnly, isReadOnly) {
      // codeOnly: the document is exactly one wrapped code fence (YAML/JSON/TXT/code).
      // body.code-only enables CSS that drops the code block's internal
      // max-height so the outer editor scroll handles long content.
      // Python decides it from the file extension (single source: main.CODE_FENCE_LANGS).
      document.body.classList.toggle("code-only", !!codeOnly);
      readOnly = !!isReadOnly;
      if (vditor) {
        vditor.setValue(md);
        applyReadOnly();
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
