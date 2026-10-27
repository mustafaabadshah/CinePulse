import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { SearchCard } from "../components/SearchCard";
import { SearchResultItem } from "../types";

describe("SearchCard Component", () => {
  it("renders episode card with title, views, duration, and free badge", () => {
    const item: SearchResultItem = {
      id: "ep_101",
      type: "episode",
      title: "Ehd E Wafa Episode 1",
      program_name: "Ehd E Wafa",
      duration: "42:15",
      views: 1540000,
      is_free: true,
      content_tier: "free",
      tags: ["Drama", "Hum TV"],
      raw: {
        is_free: true,
        duration: "42:15",
        views: 1540000,
      },
    };

    render(
      <BrowserRouter>
        <SearchCard item={item} />
      </BrowserRouter>
    );

    expect(screen.getByText("Ehd E Wafa Episode 1")).toBeInTheDocument();
    expect(screen.getByText("Show: Ehd E Wafa")).toBeInTheDocument();
    expect(screen.getByText("Free")).toBeInTheDocument();
    expect(screen.getByText("1.5M views")).toBeInTheDocument();
    expect(screen.getByText("Drama")).toBeInTheDocument();
  });

  it("renders program card with channel name and genre", () => {
    const item: SearchResultItem = {
      id: "prog_202",
      type: "program",
      title: "Hum News Live",
      channel_name: "Hum Network",
      tags: ["News", "Current Affairs"],
      raw: {
        type: "channel",
        channel_name: "Hum Network",
        info_language: "urdu",
        info_staring: "News Anchors",
      },
    };

    render(
      <BrowserRouter>
        <SearchCard item={item} />
      </BrowserRouter>
    );

    expect(screen.getByText("Hum News Live")).toBeInTheDocument();
    expect(screen.getByText("Channel")).toBeInTheDocument();
    expect(screen.getByText("News")).toBeInTheDocument();
  });

  it("renders movie card with Movie badge", () => {
    const item: SearchResultItem = {
      id: "prog_303",
      type: "program",
      title: "Teri Meri Kahaniyaan",
      channel_name: "Tamasha Movies",
      content_type: "short film, movie",
      tags: ["Comedy", "Romance"],
      raw: {
        type: "program",
        info_content_type: "short film, movie",
        channel_name: "Tamasha Movies",
        info_language: "urdu",
      },
    };

    render(
      <BrowserRouter>
        <SearchCard item={item} />
      </BrowserRouter>
    );

    expect(screen.getByText("Teri Meri Kahaniyaan")).toBeInTheDocument();
    expect(screen.getAllByText("Movie").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Tamasha Movies")).toBeInTheDocument();
  });
});
