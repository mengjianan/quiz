// JS 模块 → JSON：node tools/js2json.mjs <in.js> <out.json>
// 剥 import/export，求值模块取导出值（default 优先）
import { readFileSync, writeFileSync } from "fs";
const [inp, outp] = process.argv.slice(2);
let src = readFileSync(inp, "utf8");
src = src.replace(/^import\s[^;]+;$/gm, "");
const expNames = [...src.matchAll(/export\s+(?:const|let|var)\s+(\w+)/g)].map(m => m[1]);
const hasDefault = /export\s+default/.test(src);
src = src.replace(/export\s+default\s+/g, "let __default__ = ");
const body = src.replace(/export\s+(const|let|var)\s+/g, "$1 ");
const pick = hasDefault ? "__default__" : expNames.map(n => `typeof ${n}!=="undefined"?${n}:null`).join(" || ");
const val = new Function(`${body}\nreturn ${pick || "null"};`)();
if (val === null || val === undefined) { console.error("no export found"); process.exit(1); }
writeFileSync(outp, JSON.stringify(val));
console.log("OK", outp, Array.isArray(val) ? val.length + " items" : Object.keys(val).slice(0, 8).join(","));
