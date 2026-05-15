'use strict';

const { execSync, execFileSync } = require('child_process');

function isGitRepo(dir) {
  try {
    execSync('git rev-parse --git-dir', { cwd: dir, stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

function hasRemote(dir) {
  try {
    const out = execSync('git remote', { cwd: dir, stdio: 'pipe' }).toString().trim();
    return out.length > 0;
  } catch {
    return false;
  }
}

function gitAddCommit(dir, filename, message, scheduledAt) {
  const date = new Date(scheduledAt).toISOString();
  try {
    execFileSync('git', ['add', filename], { cwd: dir, stdio: 'pipe' });
    execFileSync('git', ['commit', '-m', message], {
      cwd: dir,
      stdio: 'pipe',
      env: { ...process.env, GIT_AUTHOR_DATE: date, GIT_COMMITTER_DATE: date },
    });
  } catch (e) {
    const msg = String(e.stderr || e.stdout || e.message || '');
    if (msg.includes('Please tell me who you are')) {
      console.error('\nGit user not configured. Run:\n  git config --global user.name "Your Name"\n  git config --global user.email "you@example.com"');
      process.exit(1);
    }
    if (!msg.includes('nothing to commit') && !msg.includes('nothing added')) {
      console.error(`\n  [git warn] ${msg.split('\n')[0]}`);
    }
  }
}

function gitPush(dir) {
  try {
    execFileSync('git', ['push'], { cwd: dir, stdio: 'pipe', timeout: 30000 });
  } catch {
    // Non-fatal: no remote, no upstream, network issue
  }
}

module.exports = { isGitRepo, hasRemote, gitAddCommit, gitPush };
