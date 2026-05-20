'use strict';

const fs = require('fs');
const path = require('path');
const { writeDocx } = require('./docx-writer');

function rand(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, Math.max(0, ms)));
}

function replaceFirst(text, search, replace) {
  const escaped = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp('\\b' + escaped + '\\b', 'i');
  return text.replace(regex, match => {
    const capFirst = match[0] >= 'A' && match[0] <= 'Z';
    return capFirst ? replace[0].toUpperCase() + replace.slice(1) : replace.toLowerCase();
  });
}

async function sleepUntil(targetIso) {
  const target = new Date(targetIso).getTime();
  while (true) {
    const remaining = target - Date.now();
    if (remaining <= 0) return;

    const chunk = Math.min(remaining, 60 * 60 * 1000);

    if (remaining > 90000) {
      const mins = Math.round(remaining / 60000);
      const h = Math.floor(mins / 60);
      const m = mins % 60;
      const label = h > 0 ? `${h}h ${m}m` : `${m}m`;
      const nextStr = new Date(target).toLocaleString();
      process.stdout.write(`\r  Waiting ${label} until ${nextStr}...     `);
    }

    await sleep(chunk);
  }
}

function clearLine() {
  process.stdout.write('\r' + ' '.repeat(70) + '\r');
}

async function executeAction(action, state) {
  const outputPath = path.join(state.outputDir, state.outputFile);

  if (action.type === 'write') {
    state.currentText = (state.currentText || '') + action.text;

    // Simulate a brief pause before saving (like a human reviewing before saving)
    await sleep(rand(2000, 7000));
    await writeDocx(outputPath, state.currentText);

    const wordCount = action.text.trim().split(/\s+/).length;
    const ts = new Date(action.scheduledAt).toLocaleTimeString();
    console.log(`  [${ts}] +${wordCount} words → "${action.label}"`);

  } else if (action.type === 'edit') {
    if (!state.currentText) {
      console.log(`  [skip] Edit — no content written yet.`);
      return;
    }

    const updated = replaceFirst(state.currentText, action.searchText, action.replaceText);
    if (updated === state.currentText) {
      console.log(`  [skip] Edit — "${action.searchText}" not found.`);
      return;
    }

    state.currentText = updated;
    await sleep(rand(1000, 4000));
    await writeDocx(outputPath, state.currentText);

    const ts = new Date(action.scheduledAt).toLocaleTimeString();
    console.log(`  [${ts}] edit  "${action.searchText}" → "${action.replaceText}"  (${action.label})`);
  }
}

async function runSimulation(state, stateFile) {
  const save = () => fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));

  const remaining = state.actions.filter(a => !a.completed);
  if (remaining.length === 0) {
    console.log('All actions already completed.');
    return;
  }

  const nextDate = new Date(remaining[0].scheduledAt).toLocaleString();
  console.log(`\n${remaining.length} actions pending. First: ${nextDate}`);
  console.log('Press Ctrl+C to pause — run again from this directory to resume.\n');

  for (const action of state.actions) {
    if (action.completed) continue;

    const now = Date.now();
    const scheduledAt = new Date(action.scheduledAt).getTime();

    if (scheduledAt > now) {
      await sleepUntil(action.scheduledAt);
      clearLine();
    } else if (now - scheduledAt > 30 * 60000) {
      const lateMin = Math.round((now - scheduledAt) / 60000);
      console.log(`  [catch-up, ${lateMin}m late]`);
    }

    await executeAction(action, state);
    action.completed = true;
    action.completedAt = new Date().toISOString();
    save();
  }
}

module.exports = { runSimulation };
