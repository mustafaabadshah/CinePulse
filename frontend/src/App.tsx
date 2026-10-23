import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { HomePage } from "./pages/HomePage";
import { SearchResultsPage } from "./pages/SearchResultsPage";
import { ResearcherDetailPage } from "./pages/ResearcherDetailPage";
import { PublicationDetailPage } from "./pages/PublicationDetailPage";
import { InstitutionDetailPage } from "./pages/InstitutionDetailPage";
import { AdminPage } from "./pages/AdminPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { HealthPage } from "./pages/HealthPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
        <Navbar />
        <main style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchResultsPage />} />
            <Route path="/researchers/:id" element={<ResearcherDetailPage />} />
            <Route path="/publications/:id" element={<PublicationDetailPage />} />
            <Route path="/institutions/:id" element={<InstitutionDetailPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/health" element={<HealthPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
};

export default App;
