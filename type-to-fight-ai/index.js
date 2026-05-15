#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');
const os = require('os');
const crypto = require('crypto');

const { askSetupQuestions } = require('./src/cli');
const { generateActions } = require('./src/scheduler');
const { runSimulation } = require('./src/simulator');
const { isGitRepo, hasRemote } = require('./src/git');

const CWD = process.cwd();

function getStatePath() {
  const hash = crypto.createHash('sha256').update(CWD).digest('hex').slice(0, 12);
  const dir = path.join(os.homedir(), '.config', 'ttfa');
  fs.mkdirSync(dir, { recursive: true });
  return path.join(dir, `state-${hash}.json`);
}

async function main() {
  if (!isGitRepo(CWD)) {
    console.error('Error: Not a git repository.\nPlease cd into a git repo before running ttfa.');
    process.exit(1);
  }

  const stateFile = getStatePath();
  let state;

  if (fs.existsSync(stateFile)) {
    state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    const done  = state.actions.filter(a => a.completed).length;
    const total = state.actions.length;
    console.log(`\nResuming simulation for: ${CWD}`);
    console.log(`Progress: ${done}/${total} actions completed.\n`);

    if (done === total) {
      console.log('Simulation already complete. Delete state to start over:');
      console.log(`  rm "${stateFile}"`);
      process.exit(0);
    }
  } else {
    console.log('\n=== Homework Simulation Setup ===\n');

    const config = await askSetupQuestions();

    const contentPath = path.isAbsolute(config.contentFile)
      ? config.contentFile
      : path.join(CWD, config.contentFile);

    if (!fs.existsSync(contentPath)) {
      console.error(`\nError: File not found: ${contentPath}`);
      process.exit(1);
    }

    const content = fs.readFileSync(contentPath, 'utf8').trim();
    if (!content) {
      console.error('\nError: Content file is empty.');
      process.exit(1);
    }

    if (!hasRemote(CWD)) {
      console.log('\nNote: No git remote found — commits will be local only (push will be skipped).');
    }

    console.log('\nGenerating schedule...');
    let actions;
    try {
      actions = generateActions(content, config);
    } catch (e) {
      console.error(`\nSchedule error: ${e.message}`);
      process.exit(1);
    }

    state = { config, content, outputFile: config.outputFile, actions };
    fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));

    const pending = actions.filter(a => !a.completed);
    console.log(`\nSchedule saved: ${actions.length} actions across ${config.activeDays} active days.`);
    if (pending.length > 0) {
      console.log(`First action: ${new Date(pending[0].scheduledAt).toLocaleString()}`);
      console.log(`Last action : ${new Date(pending[pending.length - 1].scheduledAt).toLocaleString()}`);
    }
    console.log(`\nState file: ${stateFile}`);
  }

  process.on('SIGINT', () => {
    console.log('\n\nSimulation paused. Run ttfa again from this directory to resume.');
    process.exit(0);
  });

  await runSimulation(state, stateFile);
  console.log('\nSimulation complete! All actions executed.');
}

main().catch(err => {
  console.error('\nFatal error:', err.message);
  process.exit(1);
});
