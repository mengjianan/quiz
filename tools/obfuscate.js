const fs = require('fs');
const { JavaScriptObfuscator } = require('javascript-obfuscator');

const inputFile = process.argv[2];
const outputFile = process.argv[3];
const options = {
  compact: true,
  controlFlowFlattening: true,
  deadCodeInjection: false,
  stringArray: true,
};

const js = fs.readFileSync(inputFile, 'utf8');
const result = JavaScriptObfuscator.obfuscate(js, options);
const obfuscatedCode = result.getObfuscatedCode();

fs.writeFileSync(outputFile, obfuscatedCode, 'utf8');
console.log('Obfuscation successful');
