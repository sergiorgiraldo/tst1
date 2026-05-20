'use strict';

const readline = require('readline');

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAY_MAP = {
  sun: 0, sunday: 0,
  mo: 1, mon: 1, monday: 1,
  tu: 2, tue: 2, tuesday: 2,
  we: 3, wed: 3, wednesday: 3,
  th: 4, thu: 4, thursday: 4,
  fr: 5, fri: 5, friday: 5,
  sa: 6, sat: 6, saturday: 6,
};

async function askSetupQuestions(cwd) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const ask = q => new Promise(resolve => rl.question(q, a => resolve(a.trim())));

  let contentFile = '';
  while (!contentFile) {
    contentFile = await ask('Path to your homework content file: ');
    if (!contentFile) console.log('  Required.');
  }

  const outputInput = await ask('Output filename (default: assignment.docx): ');
  const rawName = outputInput || 'assignment.docx';
  const outputFile = rawName.endsWith('.docx') ? rawName : rawName + '.docx';

  let activeDays = 0;
  while (activeDays < 1) {
    const raw = await ask('How many days should the simulation be active? (e.g., 3): ');
    activeDays = parseInt(raw, 10);
    if (isNaN(activeDays) || activeDays < 1) {
      console.log('  Enter a number >= 1.');
      activeDays = 0;
    }
  }

  const daysInput = await ask('Active weekdays (e.g., "mon-fri" or "mon,wed,fri"): ');
  const dayPattern = parseDayPattern(daysInput || 'mon-fri');

  const timeInput = await ask('Time windows in 24h (e.g., "07:00-10:00,14:00-15:00"): ');
  const timeWindows = parseTimeWindows(timeInput || '09:00-17:00');

  rl.close();

  console.log('\nConfiguration summary:');
  console.log(`  Content file : ${contentFile}`);
  console.log(`  Output file  : ${outputFile}`);
  console.log(`  Output dir   : ${cwd}`);
  console.log(`  Active days  : ${activeDays}`);
  console.log(`  Day pattern  : ${dayPattern.map(d => DAY_NAMES[d]).join(', ')}`);
  console.log(`  Time windows : ${timeWindows.map(w => `${pad(w.startHour)}:${pad(w.startMinute)}-${pad(w.endHour)}:${pad(w.endMinute)}`).join('  ')}`);

  return { contentFile, outputFile, activeDays, dayPattern, timeWindows };
}

function parseDayPattern(input) {
  const str = input.toLowerCase().trim();

  const rangeM = str.match(/^(\w+)\s*[-–]\s*(\w+)$/);
  if (rangeM) {
    const s = DAY_MAP[rangeM[1]], e = DAY_MAP[rangeM[2]];
    if (s !== undefined && e !== undefined && s <= e) {
      return Array.from({ length: e - s + 1 }, (_, i) => s + i);
    }
  }

  const days = str.split(/[,\s]+/).map(p => DAY_MAP[p.trim()]).filter(d => d !== undefined);
  return days.length ? days : [1, 2, 3, 4, 5];
}

function parseTimeWindows(input) {
  const result = [];
  for (const part of input.split(',')) {
    const m = part.trim().match(/(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})/);
    if (m) {
      result.push({ startHour: +m[1], startMinute: +m[2], endHour: +m[3], endMinute: +m[4] });
    }
  }
  return result.length ? result : [{ startHour: 9, startMinute: 0, endHour: 12, endMinute: 0 }];
}

function pad(n) { return String(n).padStart(2, '0'); }

module.exports = { askSetupQuestions };
