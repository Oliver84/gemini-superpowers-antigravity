#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const AGENT_SOURCE = path.join(REPO_ROOT, '.agent');
const TARGET_DIR = process.cwd();
const TARGET_AGENT = path.join(TARGET_DIR, '.agent');

console.log('🚀 Installing Gemini Superpowers Antigravity...');

if (!fs.existsSync(AGENT_SOURCE)) {
  console.error('❌ Error: Could not find .agent directory in source.');
  process.exit(1);
}

// Copy .agent directory
console.log(`📂 Copying framework to ${TARGET_AGENT}...`);
try {
  // Use recursive copy (Node.js 16.7.0+)
  fs.cpSync(AGENT_SOURCE, TARGET_AGENT, { recursive: true });
} catch (e) {
  console.error('❌ Failed to copy files:', e.message);
  process.exit(1);
}

// Initialize config
const CONFIG_PATH = path.join(TARGET_AGENT, 'config.json');
if (!fs.existsSync(CONFIG_PATH)) {
  console.log('⚙️  Initializing config.json...');
  fs.writeFileSync(CONFIG_PATH, JSON.stringify({ execution_backend: 'gemini' }, null, 2));
}

console.log('\n✅ Installation complete!');
console.log('👉 Next steps:');
console.log('1. Open this folder in Google Antigravity.');
console.log('2. Run `/superpowers-reload` to load the new skills.');
