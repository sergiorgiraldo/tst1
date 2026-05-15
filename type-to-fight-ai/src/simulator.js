'use strict';

const fs = require('fs');
const path = require('path');
const { gitAddCommit, gitPush } = require('./git');

function rand(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, Math.max(0, ms)));
}

// Replaces the first case-insensitive whole-word occurrence of `search` in `text`
function replaceFirst(text, search, replace) {
  const escaped = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp('\\b' + escaped + '\\b', 'i');
  return text.replace(regex, match => {
    const capFirst = match[0] >= 'A' && match[0] <= 'Z';
    return capFirst ? replace[0].toUpperCase() + replace.slice(1) : replace.toLowerCase();
  });
}

// Sleeps until `targetIso` using chunked setTimeout (1h max per chunk = no CPU usage).
// Prints a one-line countdown that overwrites itself.
async function sleepUntil(targetIso) {
  const target = new Date(targetIso).getTime();
  while (true) {
    const remaining = target - Date.now();
    if (remaining <= 0) return;

    const chunk = Math.min(remaining, 60 * 60 * 1000);

    if (remaining > 90000) { // only print if more than 90s away
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

async function executeAction(action, state, cwd) {
  const outputFile = path.join(cwd, state.outputFile);

  if (action.type === 'write') {
    fs.appendFileSync(outputFile, action.text);

    // Simulate "reviewing before committing"
    await sleep(rand(2000, 7000));

    gitAddCommit(cwd, state.outputFile, action.commitMsg, action.scheduledAt);
    gitPush(cwd);

    const wordCount = action.text.trim().split(/\s+/).length;
    const ts = new Date(action.scheduledAt).toLocaleTimeString();
    console.log(`  [${ts}] +${wordCount} words → "${action.commitMsg}"`);

  } else if (action.type === 'edit') {
    if (!fs.existsSync(outputFile)) {
      console.log(`  [skip] Edit — output file not found yet.`);
      return;
    }

    const current = fs.readFileSync(outputFile, 'utf8');
    const updated = replaceFirst(current, action.searchText, action.replaceText);

    if (updated === current) {
      console.log(`  [skip] Edit — "${action.searchText}" not found in file.`);
      return;
    }

    fs.writeFileSync(outputFile, updated);
    await sleep(rand(1000, 4000));

    gitAddCommit(cwd, state.outputFile, action.commitMsg, action.scheduledAt);
    gitPush(cwd);

    const ts = new Date(action.scheduledAt).toLocaleTimeString();
    console.log(`  [${ts}] edit  "${action.searchText}" → "${action.replaceText}"  (${action.commitMsg})`);
  }
}

async function runSimulation(state, stateFile) {
  const cwd = process.cwd();
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
      // Catch-up: action is more than 30 min overdue — execute immediately but note it
      const lateMin = Math.round((now - scheduledAt) / 60000);
      console.log(`  [catch-up, ${lateMin}m late]`);
    }

    await executeAction(action, state, cwd);
    action.completed = true;
    action.completedAt = new Date().toISOString();
    save();
  }
}

module.exports = { runSimulation };
