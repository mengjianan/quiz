// 从单文件 HTML 应用提取全部题库数组字面量（JS 语法，由 node 求值）
// node tools/jsx_extract.mjs <in.html> <out.json>  → 输出 {变量名: 值, ...}
import { readFileSync, writeFileSync } from "fs";
const [inp, outp] = process.argv.slice(2);
const src = readFileSync(inp, "utf8");

// 从任意起始括号做「字符串/注释感知」的配对扫描
function matchBracket(s, start) {
  const open = s[start], close = open === "[" ? "]" : "}";
  let depth = 0, i = start;
  while (i < s.length) {
    const c = s[i];
    if (c === "'" || c === '"' || c === "`") {
      const q = c; i++;
      while (i < s.length) {
        if (s[i] === "\\") { i += 2; continue; }
        if (s[i] === q) break;
        i++;
      }
      i++; continue;
    }
    if (c === "/" && s[i + 1] === "/") { while (i < s.length && s[i] !== "\n") i++; continue; }
    if (c === "/" && s[i + 1] === "*") { i += 2; while (i < s.length && !(s[i] === "*" && s[i + 1] === "/")) i++; i += 2; continue; }
    if (c === open) depth++;
    else if (c === close) { depth--; if (depth === 0) return i; }
    i++;
  }
  return -1;
}

const anchors = [...src.matchAll(/(?:const|let|var)\s+(\w+)\s*=\s*([\[{])/g)];
console.log("anchors:", anchors.map(m => m[1]).join(","));
const out = {};
for (const m of anchors) {
  const start = m.index + m[0].length - 1;
  const end = matchBracket(src, start);
  if (end <= 0) continue;
  try {
    const val = new Function(`return ${src.slice(start, end + 1)};`)();
    const arr = Array.isArray(val) ? val : null;
    if (arr && arr.length >= 5 && arr.every(x => x && typeof x === "object")) {
      const keys = Object.keys(arr[0]);
      const looksQuestion = keys.some(k => ["stem", "question", "q", "scenario", "title", "id"].includes(k));
      if (looksQuestion) { out[m[1]] = val; console.log(`bank ${m[1]}: ${arr.length} items, keys=${keys.slice(0,10).join(",")}`); }
    }
  } catch (e) { /* 求值失败则跳过 */ }
}
if (!Object.keys(out).length) { console.error("no banks found"); process.exit(1); }
writeFileSync(outp, JSON.stringify(out));
console.log("OK ->", outp, Object.keys(out).join(","));
