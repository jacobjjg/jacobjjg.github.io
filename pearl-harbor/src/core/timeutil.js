// Simulation time helpers.
//
// SIM TIME `t` is a Number: seconds after 1941-12-07 00:00:00 Hawaii time (HST, then UTC-10:30).
//   07:55 on the day of the attack = 28500.   26 Nov 1941 06:00 = -11 days + 6 h = -928800.
// Japanese records use Tokyo time = Hawaii time + 19 h 30 min.

export const DAY = 86400;
export const HOUR = 3600;
export const MIN = 60;

/** Shader time epoch: uniforms.uSimTime = sim - SIM_EPOCH so float32 keeps millisecond precision during the attack. */
export const SIM_EPOCH = 8 * HOUR;

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const BASE_UTC_MS = Date.UTC(1941, 11, 7); // treated as a naive local calendar date

/**
 * Parse a time into sim seconds.
 *   T('07:55')  T('07:55:30')  T('7:55:30.5')  T('1941-11-26 06:00')  T('1941-12-08T12:30:00')  T(28500) -> 28500
 */
export function T(v) {
  if (typeof v === 'number') return v;
  if (v == null) return NaN;
  const s = String(v).trim();
  let dayOffset = 0, clock = s;
  const m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T]+(.*))?$/);
  if (m) {
    dayOffset = Math.round((Date.UTC(+m[1], +m[2] - 1, +m[3]) - BASE_UTC_MS) / 86400000);
    clock = m[4] || '00:00';
  }
  const p = clock.split(':').map(Number);
  if (p.some((x) => !Number.isFinite(x))) return NaN;
  const sec = (p[0] || 0) * 3600 + (p[1] || 0) * 60 + (p[2] || 0);
  return dayOffset * DAY + sec;
}

const pad = (n) => String(n).padStart(2, '0');

/** '07:55' or '07:55:30' (Hawaii time of day). */
export function fmtClock(t, withSeconds = false) {
  const s = ((Math.floor(t) % DAY) + DAY) % DAY;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  return withSeconds ? `${pad(h)}:${pad(m)}:${pad(ss)}` : `${pad(h)}:${pad(m)}`;
}

/** { year, month (1-12), day, weekday (0=Sunday), monthName, weekdayName } of the Hawaii calendar date at sim time t. */
export function dateParts(t) {
  const d = new Date(BASE_UTC_MS + Math.floor(t / DAY) * 86400000);
  return {
    year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate(), weekday: d.getUTCDay(),
    monthName: MONTH_NAMES[d.getUTCMonth()], weekdayName: WEEKDAYS[d.getUTCDay()],
  };
}

/** 'Sunday, December 7, 1941' */
export function fmtDate(t, withWeekday = true) {
  const p = dateParts(t);
  return `${withWeekday ? p.weekdayName + ', ' : ''}${p.monthName} ${p.day}, ${p.year}`;
}

/** Tokyo clock/date for the same instant (Hawaii + 19.5 h): { clock: '03:25', date: 'December 8, 1941' }. */
export function tokyo(t) {
  const tt = t + 19.5 * HOUR;
  return { clock: fmtClock(tt), date: fmtDate(tt, false) };
}

/** '1 h 05 min', '45 s' ... for durations. */
export function fmtDuration(sec) {
  const s = Math.round(Math.abs(sec));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} min ${pad(s % 60)} s`;
  return `${Math.floor(s / 3600)} h ${pad(Math.floor((s % 3600) / 60))} min`;
}
