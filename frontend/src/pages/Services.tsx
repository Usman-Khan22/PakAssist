import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { categories, services } from "../data";
import Header from "../components/Header";
import Footer from "../components/Footer";
import ServiceGrid from "../components/ServiceGrid";

export default function Services() {
  const [params] = useSearchParams();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(
    params.get("category") || "All Services",
  );
  const filtered = services.filter(
    (s) =>
      (category === "All Services" || s.category === category) &&
      `${s.title} ${s.description}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <Header />
      <main>
        <section className="page-band">
          <div className="container">
            <small className="eyebrow">YOUR NEXT STEP</small>
            <h1>Government Services</h1>
            <p>
              Find clear, practical guidance for the services that matter to
              you.
            </p>
          </div>
        </section>
        <section className="section services-page">
          <div className="container">
            <div className="directory-toolbar">
              <div className="directory-search">
                <Search size={18} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search services..."
                />
              </div>
              <span className="result-count">{filtered.length} services</span>
            </div>
            <div className="filter-pills">
              {["All Services", ...categories].map((x) => (
                <button
                  className={category === x ? "selected" : ""}
                  onClick={() => setCategory(x)}
                  key={x}
                >
                  {x}
                </button>
              ))}
            </div>
            {filtered.length ? (
              <ServiceGrid services={filtered} />
            ) : (
              <div className="empty-state">
                <Search size={28} />
                <h3>No services found</h3>
                <p>Try another search or clear the category filter.</p>
                <button
                  onClick={() => {
                    setQuery("");
                    setCategory("All Services");
                  }}
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
