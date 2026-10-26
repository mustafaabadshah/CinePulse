/**
 * Canonical duration formatter for Tamasha Catalog Explorer.
 *
 * Converts numeric seconds into clean, human-readable OTT runtime strings:
 * - < 1 hour: 'M:SS' or '0:SS' (e.g. 39 -> '0:39', 2370 -> '39:30', 1538 -> '25:38')
 * - >= 1 hour: 'H:MM:SS' (e.g. 4779 -> '1:19:39', 3600 -> '1:00:00')
 * - Gracefully handles null, undefined, NaN, and negative inputs without crashing.
 */

export function formatDuration(
  seconds?: number | null,
  rawFallback?: string | null
): string {
  // If valid numeric seconds provided
  if (seconds !== undefined && seconds !== null && !isNaN(seconds)) {
    const totalSec = Math.floor(seconds);
    if (totalSec < 0) return "";
    
    const hours = Math.floor(totalSec / 3600);
    const minutes = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;

    const paddedSecs = secs.toString().padStart(2, "0");

    if (hours > 0) {
      const paddedMins = minutes.toString().padStart(2, "0");
      return `${hours}:${paddedMins}:${paddedSecs}`;
    }

    return `${minutes}:${paddedSecs}`;
  }

  // Graceful fallback to raw string if provided
  if (rawFallback && typeof rawFallback === "string") {
    const trimmed = rawFallback.trim();
    if (!trimmed || trimmed.toLowerCase() === "null") return "";

    // If pure integer string like "1538"
    if (/^\d+$/.test(trimmed)) {
      const parsedSec = parseInt(trimmed, 10);
      return formatDuration(parsedSec);
    }

    // If HH:MM:SS format like "00:39:30", simplify leading zeroes
    const parts = trimmed.split(":");
    if (parts.length === 3) {
      const h = parseInt(parts[0], 10);
      const m = parseInt(parts[1], 10);
      const s = parseInt(parts[2], 10);
      if (!isNaN(h) && !isNaN(m) && !isNaN(s)) {
        return formatDuration(h * 3600 + m * 60 + s);
      }
    } else if (parts.length === 2) {
      const m = parseInt(parts[0], 10);
      const s = parseInt(parts[1], 10);
      if (!isNaN(m) && !isNaN(s)) {
        return formatDuration(m * 60 + s);
      }
    }

    return trimmed;
  }

  return "";
}

/**
 * Returns true if the video duration represents a short promotional teaser or clip (< 60s).
 */
export function isTeaserOrClip(seconds?: number | null): boolean {
  if (seconds === undefined || seconds === null || isNaN(seconds)) return false;
  return seconds > 0 && seconds < 60;
}
