import React, { useState, useEffect, useCallback } from "react";
import { searchSimilar, searchByText, getFilters, checkHealth } from "./api/client";
import DropZone from "./components/DropZone";
import ResultsGrid from "./components/ResultsGrid";
import ImageDetail from "./components/ImageDetail";
import FilterBar from "./components/FilterBar";
import StatusBar from "./components/StatusBar";

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

export default function App() {
  const [state, setState] = useState("idle"); // idle | searching | results | detail
  const [results, setResults] = useState(null);
  const [selectedResult, setSelectedResult] = useState(null);
  const [filters, setFilters] = useState({});
  const [filterOptions, setFilterOptions] = useState(null);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [queryFile, setQueryFile] = useState(null);
  const [textQuery, setTextQuery] = useState("");
  const [isDark, setIsDark] = useState(
    () => (localStorage.getItem("theme") ?? "dark") === "dark"
  );

  // Apply theme to <html> and persist to localStorage
  useEffect(() => {
    const theme = isDark ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [isDark]);

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  // Load filter options on mount
  useEffect(() => {
    getFilters()
      .then(setFilterOptions)
      .catch(() => {});
  }, []);

  const handleSearch = useCallback(
    async (file) => {
      setQueryFile(file);
      setState("searching");
      setError(null);
      setResults(null);

      try {
        const data = await searchSimilar(file, filters);
        setResults(data);
        setState("results");
      } catch (err) {
        setError(err.message);
        setState("idle");
      }
    },
    [filters]
  );

  const handleTextSearch = useCallback(
    async (e) => {
      e.preventDefault();
      if (!textQuery.trim()) return;
      setState("searching");
      setError(null);
      setResults(null);
      setQueryFile(null);

      try {
        const data = await searchByText(textQuery.trim(), filters);
        setResults(data);
        setState("results");
      } catch (err) {
        setError(err.message);
        setState("idle");
      }
    },
    [textQuery, filters]
  );

  const handleResultClick = useCallback((result) => {
    setSelectedResult(result);
    setState("detail");
  }, []);

  const handleBack = useCallback(() => {
    setSelectedResult(null);
    setState("results");
  }, []);

  const handleNewSearch = useCallback(() => {
    setState("idle");
    setResults(null);
    setSelectedResult(null);
    setQueryFile(null);
    setTextQuery("");
  }, []);

  const handleFilterChange = useCallback(
    (newFilters) => {
      setFilters(newFilters);
      if (queryFile) {
        handleSearch(queryFile);
      }
    },
    [queryFile, handleSearch]
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>Medical Microscopy Similarity Engine</h1>
        <div className="header-actions">
          {state !== "idle" && (
            <button className="btn btn-secondary" onClick={handleNewSearch}>
              New Search
            </button>
          )}
          <button
            className="theme-toggle"
            onClick={() => setIsDark((d) => !d)}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDark ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {state === "idle" && (
          <>
            <DropZone onFileDrop={handleSearch} />
            <div className="text-search">
              <div className="text-search-divider">or search by description</div>
              <form className="text-search-form" onSubmit={handleTextSearch}>
                <input
                  type="text"
                  className="text-search-input"
                  placeholder="e.g. melanoma with irregular border"
                  value={textQuery}
                  onChange={(e) => setTextQuery(e.target.value)}
                />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!textQuery.trim()}
                >
                  Search
                </button>
              </form>
            </div>
          </>
        )}

        {state === "searching" && (
          <div className="loading">
            <div className="spinner" />
            <p>Analyzing image and searching for similar cases...</p>
          </div>
        )}

        {(state === "results" || state === "detail") && results && (
          <>
            {filterOptions && (
              <FilterBar
                options={filterOptions}
                filters={filters}
                onChange={handleFilterChange}
              />
            )}

            {state === "results" && (
              <ResultsGrid
                results={results.results}
                onResultClick={handleResultClick}
              />
            )}

            {state === "detail" && selectedResult && (
              <ImageDetail result={selectedResult} onBack={handleBack} />
            )}
          </>
        )}
      </main>

      <StatusBar health={health} results={results} />
    </div>
  );
}
