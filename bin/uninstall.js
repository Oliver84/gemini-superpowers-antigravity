#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const TARGET_DIR = process.cwd();
const TARGET_AGENT = path.join(TARGET_DIR, '.agent');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('🗑️  Uninstalling Gemini Superpowers Antigravity...');
console.log(`📍 Target: ${TARGET_AGENT}`);

if (!fs.existsSync(TARGET_AGENT)) {
  console.log('❌ Superpowers framework not found in this directory.');
  process.exit(0);
}

rl.question('⚠️  Are you sure you want to delete the .agent folder? (y/N) ', (answer) => {
  if (answer.toLowerCase() === 'y') {
    try {
      // Use recursive remove (Node.js 14.14.0+)
      fs.rmSync(TARGET_AGENT, { recursive: true, force: true });
      console.log('✅ Uninstalled successfully.');
    } catch (e) {
      console.error('❌ Failed to uninstall:', e.message);
    }
  } else {
    console.log('❌ Uninstall cancelled.');
  }
  rl.close();
});
