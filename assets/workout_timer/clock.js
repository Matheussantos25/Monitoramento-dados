/* Timestamp arithmetic keeps elapsed time independent of delayed UI ticks. */
class WorkoutClock {
  constructor(data = {}) { this.elapsed = data.elapsed || 0; this.started = data.started ?? null; }
  used(now) { return this.elapsed + (this.started === null ? 0 : Math.max(0, now - this.started)); }
  start(now) { if (this.started === null) this.started = now; }
  pause(now) { this.elapsed = this.used(now); this.started = null; }
  reset() { this.elapsed = 0; this.started = null; }
  remaining(totalSeconds, now) { return Math.max(0, totalSeconds * 1000 - this.used(now)); }
}
if (typeof module !== 'undefined') module.exports = {WorkoutClock};
