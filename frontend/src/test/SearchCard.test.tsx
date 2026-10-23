import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { SearchCard } from "../components/SearchCard";
import { SearchResultItem } from "../types";

describe("SearchCard Component", () => {
  it("renders researcher card with name, tags, and verified badge", () => {
    const item: SearchResultItem = {
      id: "res_elena_rostova_mit",
      type: "researcher",
      title: "Dr. Elena Rostova",
      subtitle: "MIT • United States",
      snippet: "Principal investigator specializing in diffusion models.",
      tags: ["Generative AI", "Computer Vision"],
      is_synthetic: true,
      raw: { contact_email_verified: true },
    };

    render(
      <BrowserRouter>
        <SearchCard item={item} />
      </BrowserRouter>
    );

    expect(screen.getByText("Dr. Elena Rostova")).toBeInTheDocument();
    expect(screen.getByText("MIT • United States")).toBeInTheDocument();
    expect(screen.getByText("Verified Contact")).toBeInTheDocument();
    expect(screen.getByText("Synthetic")).toBeInTheDocument();
    expect(screen.getByText("Generative AI")).toBeInTheDocument();
  });

  it("renders publication card with venue and authors", () => {
    const item: SearchResultItem = {
      id: "pub_diffusion_flow_2025",
      type: "publication",
      title: "Continuous Flow Matching for Ultra-Fast Diffusion",
      subtitle: "Elena Rostova, Haruto Takahashi • CVPR 2025 (2025)",
      snippet: "We present a unified formulation for generative synthesis.",
      tags: ["Diffusion Models"],
      is_synthetic: true,
      raw: {},
    };

    render(
      <BrowserRouter>
        <SearchCard item={item} />
      </BrowserRouter>
    );

    expect(screen.getByText("Continuous Flow Matching for Ultra-Fast Diffusion")).toBeInTheDocument();
    expect(screen.getByText("publication")).toBeInTheDocument();
  });
});
