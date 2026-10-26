import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MediaImage, resolveImageUrl } from "../components/MediaImage";

describe("resolveImageUrl", () => {
  it("resolves relative uploads paths to Tamasha S3 CDN", () => {
    const input = "uploads/episodes/PgP658VykOd.webp";
    const expected = "https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/PgP658VykOd.webp";
    expect(resolveImageUrl(input)).toBe(expected);
  });

  it("handles leading slash in relative paths", () => {
    const input = "/uploads/episodes/PgP658VykOd.webp";
    const expected = "https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/PgP658VykOd.webp";
    expect(resolveImageUrl(input)).toBe(expected);
  });

  it("migrates legacy jazztv domain to Tamasha S3 CDN", () => {
    const input = "https://srv2.jazztv.pk/jazzlive/uploads/episodes/abc.webp";
    const expected = "https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/abc.webp";
    expect(resolveImageUrl(input)).toBe(expected);
  });

  it("preserves already fully qualified S3 URLs", () => {
    const s3Url = "https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/xyz.webp";
    expect(resolveImageUrl(s3Url)).toBe(s3Url);
  });

  it("returns null for null, undefined, or empty strings", () => {
    expect(resolveImageUrl(null)).toBeNull();
    expect(resolveImageUrl(undefined)).toBeNull();
    expect(resolveImageUrl("")).toBeNull();
    expect(resolveImageUrl("   ")).toBeNull();
  });
});

describe("MediaImage Component", () => {
  it("renders image tag with resolved S3 URL when valid source is provided", () => {
    render(
      <MediaImage
        src="uploads/episodes/test.webp"
        alt="Test Episode"
        type="episode"
      />
    );
    const img = screen.getByRole("img", { hidden: true });
    expect(img).toBeDefined();
    expect(img.getAttribute("src")).toBe(
      "https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/test.webp"
    );
  });

  it("renders designed fallback when src is null or empty", () => {
    render(
      <MediaImage
        src={null}
        alt="Ehd E Wafa Drama"
        title="Ehd E Wafa"
        type="program"
      />
    );
    const placeholder = screen.getByRole("img", { name: "Ehd E Wafa Drama" });
    expect(placeholder).toBeDefined();
    expect(screen.getByText("Show")).toBeDefined();
    expect(screen.getByText("Ehd E Wafa")).toBeDefined();
  });

  it("falls back to designed placeholder when image fires onError without crashing", () => {
    render(
      <MediaImage
        src="https://non-existent-domain-404.com/bad.png"
        alt="Broken Media"
        type="channel"
        title="Hum News"
      />
    );
    const img = screen.getByRole("img", { hidden: true });
    fireEvent.error(img);

    // After error, fallback container should be active with Live Channel
    expect(screen.getByText("Live Channel")).toBeDefined();
    expect(screen.getByText("Hum News")).toBeDefined();
  });
});
