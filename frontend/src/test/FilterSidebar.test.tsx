import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FilterSidebar } from "../components/FilterSidebar";

describe("FilterSidebar Component", () => {
  it("renders facet groups and trigger filter changes on click", () => {
    const facets = {
      country: {
        "United States": 4,
        "United Kingdom": 2,
      },
    };
    const activeFilters = {};
    const onFilterChange = vi.fn();
    const onClearFilters = vi.fn();

    render(
      <FilterSidebar
        facets={facets}
        activeFilters={activeFilters}
        onFilterChange={onFilterChange}
        onClearFilters={onClearFilters}
      />
    );

    expect(screen.getByText("United States")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();

    fireEvent.click(screen.getByText("United States"));
    expect(onFilterChange).toHaveBeenCalledWith("country", "United States");
  });
});
