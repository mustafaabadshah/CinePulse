import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FilterSidebar } from "../components/FilterSidebar";

describe("FilterSidebar Component", () => {
  it("renders media facet groups and triggers filter changes on click", () => {
    const facets = {
      genre: {
        Drama: 120,
        Comedy: 45,
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

    expect(screen.getByText("Drama")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Drama"));
    expect(onFilterChange).toHaveBeenCalledWith("genre", "Drama");
  });
});
