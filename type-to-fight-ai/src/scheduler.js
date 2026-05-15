'use strict';

const EDIT_PAIRS = [
  ['however', 'but'],
  ['therefore', 'thus'],
  ['additionally', 'also'],
  ['furthermore', 'moreover'],
  ['demonstrate', 'show'],
  ['utilize', 'use'],
  ['significant', 'important'],
  ['numerous', 'many'],
  ['because', 'since'],
  ['although', 'though'],
  ['requires', 'needs'],
  ['obtain', 'get'],
];

const EARLY_MSGS  = ['Start assignment', 'Add introduction', 'Begin draft', 'Initial work'];
const MID_MSGS    = ['Continue writing', 'Add content', 'More progress', 'Keep going', 'Add section', 'Work on draft'];
const LATE_MSGS   = ['Add conclusion', 'Final section', 'Nearly done', 'Finishing up'];
const EDIT_MSGS   = ['Fix wording', 'Revise section', 'Edit paragraph', 'Update text', 'Refine draft'];
const REVERT_MSGS = ['Undo change', 'Revert edit', 'Restore original'];

function rand(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function addMin(date, minutes) {
  return new Date(date.getTime() + minutes * 60000);
}

function setTimeLocal(date, hour, minute) {
  const d = new Date(date);
  d.setHours(hour, minute, rand(0, 59), rand(0, 999));
  return d;
}

function pickMsg(pool) {
  return pool[rand(0, pool.length - 1)];
}

function commitMsg(progress) {
  if (progress < 0.2) return pickMsg(EARLY_MSGS);
  if (progress > 0.8) return pickMsg(LATE_MSGS);
  return pickMsg(MID_MSGS);
}

function findEditPair(text) {
  const lower = text.toLowerCase();
  const shuffledPairs = shuffle(EDIT_PAIRS);
  for (const [word, replacement] of shuffledPairs) {
    if (new RegExp('\\b' + word + '\\b').test(lower)) {
      return { searchText: word, replaceText: replacement };
    }
  }
  return null;
}

function selectActiveDates({ activeDays, dayPattern, timeWindows }) {
  const candidates = [];
  const cursor = new Date();
  cursor.setDate(cursor.getDate() + 1);
  cursor.setHours(0, 0, 0, 0);

  // Collect up to 4x the needed days as candidates (search max 90 days out)
  for (let i = 0; i < 90 && candidates.length < activeDays * 4; i++) {
    if (dayPattern.includes(cursor.getDay())) {
      candidates.push(new Date(cursor));
    }
    cursor.setDate(cursor.getDate() + 1);
  }

  if (candidates.length < activeDays) {
    throw new Error(
      `Only found ${candidates.length} valid days in the next 90 days matching your schedule. ` +
      `Needed ${activeDays}. Try a broader day pattern.`
    );
  }

  // Randomly pick activeDays and sort chronologically
  return shuffle(candidates).slice(0, activeDays).sort((a, b) => a - b).map(date => ({
    date,
    windows: timeWindows
      .map(w => ({
        start: setTimeLocal(date, w.startHour, w.startMinute),
        end:   setTimeLocal(date, w.endHour,   w.endMinute),
      }))
      .filter(w => w.end > w.start && (w.end - w.start) >= 10 * 60000), // at least 10 min
  }));
}

function generateActions(content, config) {
  const activeDates = selectActiveDates(config);
  const words = content.split(/\s+/).filter(Boolean);
  const totalWords = words.length;

  // Count how many write bursts we'll have total
  const sessions = [];
  let totalBursts = 0;

  for (const { windows } of activeDates) {
    for (const window of windows) {
      const winMin = (window.end - window.start) / 60000;
      const numBursts = winMin < 30 ? 1 : winMin < 60 ? 2 : winMin < 120 ? 3 : 4;
      totalBursts += numBursts;
      sessions.push({ window, numBursts });
    }
  }

  if (totalBursts === 0) {
    throw new Error('No valid sessions generated. Check your day pattern and time windows.');
  }

  const wordsPerBurst = Math.ceil(totalWords / totalBursts);
  const actions = [];
  let wordPos = 0;
  let writtenText = ''; // accumulates what has been "written" so far (for edit planning)

  for (let si = 0; si < sessions.length; si++) {
    const { window, numBursts } = sessions[si];
    const winMs = window.end - window.start;

    // Space bursts evenly across 70% of window, starting after a random offset in first 20%
    const usableMs = winMs * 0.70;
    const startOffset = rand(0, winMs * 0.15);
    const gapMs = numBursts > 1 ? usableMs / (numBursts - 1) : 0;

    for (let b = 0; b < numBursts; b++) {
      if (wordPos >= totalWords) break;

      const isLastBurst = wordPos + wordsPerBurst >= totalWords;
      const burstWords = isLastBurst
        ? words.slice(wordPos)
        : words.slice(wordPos, wordPos + wordsPerBurst);

      // Add newline between sessions, space within a session
      const separator = b === numBursts - 1 ? '\n' : ' ';
      const burstText = burstWords.join(' ') + separator;

      const burstOffset = startOffset + b * (gapMs + rand(-gapMs * 0.15, gapMs * 0.15));
      const burstTime = new Date(window.start.getTime() + Math.max(0, burstOffset));

      actions.push({
        id: actions.length,
        type: 'write',
        text: burstText,
        commitMsg: commitMsg(wordPos / totalWords),
        scheduledAt: burstTime.toISOString(),
        completed: false,
      });

      writtenText += burstText;
      wordPos += burstWords.length;
    }

    // 40% chance: schedule an edit + revert within this window
    if (writtenText.length > 100 && Math.random() < 0.4) {
      const pair = findEditPair(writtenText);

      if (pair) {
        // Edit happens in the latter half of the window
        const editTime = addMin(window.start, rand(
          Math.floor(winMs / 60000 * 0.5),
          Math.floor(winMs / 60000 * 0.75)
        ));

        if (editTime < window.end) {
          actions.push({
            id: actions.length,
            type: 'edit',
            searchText: pair.searchText,
            replaceText: pair.replaceText,
            commitMsg: pickMsg(EDIT_MSGS),
            scheduledAt: editTime.toISOString(),
            completed: false,
          });

          const revertTime = addMin(editTime, rand(5, 15));
          if (revertTime < window.end) {
            actions.push({
              id: actions.length,
              type: 'edit',
              searchText: pair.replaceText,
              replaceText: pair.searchText,
              commitMsg: pickMsg(REVERT_MSGS),
              scheduledAt: revertTime.toISOString(),
              completed: false,
            });
          }
        }
      }
    }
  }

  // Sort all actions chronologically and reassign IDs
  return actions
    .sort((a, b) => new Date(a.scheduledAt) - new Date(b.scheduledAt))
    .map((a, i) => ({ ...a, id: i }));
}

module.exports = { generateActions };
