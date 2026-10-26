import { describe, it, expect } from "vitest";
import { formatDuration, isTeaserOrClip } from "../utils/formatDuration";

describe("formatDuration Utility", () => {
  it("formats zero seconds correctly", () => {
    expect(formatDuration(0)).toBe("0:00");
  });

  it("formats a few seconds correctly", () => {
    expect(formatDuration(5)).toBe("0:05");
  });

  it("formats 32 and 39 seconds correctly (flagged teaser examples)", () => {
    expect(formatDuration(32)).toBe("0:32");
    expect(formatDuration(39)).toBe("0:39");
  });

  it("formats 59 seconds correctly", () => {
    expect(formatDuration(59)).toBe("0:59");
  });

  it("formats 60 seconds (1 minute boundary) correctly", () => {
    expect(formatDuration(60)).toBe("1:00");
  });

  it("formats 90 seconds correctly", () => {
    expect(formatDuration(90)).toBe("1:30");
  });

  it("formats 32 minutes (1920 seconds) correctly", () => {
    expect(formatDuration(1920)).toBe("32:00");
  });

  it("formats 39 minutes (2340 seconds) correctly", () => {
    expect(formatDuration(2340)).toBe("39:00");
  });

  it("formats 59 minutes, 59 seconds (3599 seconds) correctly", () => {
    expect(formatDuration(3599)).toBe("59:59");
  });

  it("formats exactly one hour (3600 seconds) correctly", () => {
    expect(formatDuration(3600)).toBe("1:00:00");
  });

  it("formats multiple hours (e.g. 5400s = 1h 30m, 7200s = 2h) correctly", () => {
    expect(formatDuration(5400)).toBe("1:30:00");
    expect(formatDuration(7200)).toBe("2:00:00");
    expect(formatDuration(4779)).toBe("1:19:39");
  });

  it("handles null, undefined, NaN, and negative inputs gracefully", () => {
    expect(formatDuration(null)).toBe("");
    expect(formatDuration(undefined)).toBe("");
    expect(formatDuration(NaN)).toBe("");
    expect(formatDuration(-15)).toBe("");
  });

  it("falls back to raw string parsing when numeric seconds is absent", () => {
    expect(formatDuration(null, "1538")).toBe("25:38");
    expect(formatDuration(undefined, "00:39:30")).toBe("39:30");
    expect(formatDuration(undefined, "00:00:32")).toBe("0:32");
    expect(formatDuration(undefined, "01:19:39")).toBe("1:19:39");
    expect(formatDuration(undefined, "387")).toBe("6:27");
  });

  it("identifies short teasers and clips under 60 seconds", () => {
    expect(isTeaserOrClip(32)).toBe(true);
    expect(isTeaserOrClip(39)).toBe(true);
    expect(isTeaserOrClip(59)).toBe(true);
    expect(isTeaserOrClip(60)).toBe(false);
    expect(isTeaserOrClip(2370)).toBe(false);
    expect(isTeaserOrClip(null)).toBe(false);
  });
});
