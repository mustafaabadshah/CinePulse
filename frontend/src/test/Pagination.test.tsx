import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Pagination } from "../components/Pagination";

describe("Pagination Component", () => {
  it("renders page info and fires onPageChange", () => {
    const onPageChange = vi.fn();

    render(
      <Pagination
        page={1}
        totalPages={5}
        totalHits={48}
        limit={10}
        onPageChange={onPageChange}
      />
    );

    expect(screen.getByText("Page 1 of 5")).toBeInTheDocument();
    expect(screen.getByText("1-10")).toBeInTheDocument();
    expect(screen.getByText("48")).toBeInTheDocument();

    const nextBtn = screen.getByText("Next");
    fireEvent.click(nextBtn);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
