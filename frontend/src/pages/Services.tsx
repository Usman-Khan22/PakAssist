import { copy } from "../translations";
import { useLanguage } from "../language";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { categories, categoryLabels, services } from "../data";
import Header from "../components/Header";
import Footer from "../components/Footer";
import ServiceGrid from "../components/ServiceGrid";

export default function Services() {
  const { t, localize } = useLanguage();
  const [params] = useSearchParams();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(
    params.get("category") || copy.allServices.en,
  );
  const filtered = services.filter(
    (s) =>
      (category === copy.allServices.en || s.category === category) &&
      `${s.title.en} ${s.title.ur} ${s.description.en} ${s.description.ur}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <Header />
      <main>
        <section className="page-band">
          <div className="container">
            <small className="eyebrow"> {t.yourNextStep2} </small>
            <h1> {t.governmentServices2} </h1>
            <p> {t.findClearPracticalGuidanceForTheServicesThatMatter} </p>
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
                  placeholder={t.searchServices}
                />
              </div>
              <span className="result-count">{filtered.length} {t.services2} </span>
            </div>
            <div className="filter-pills">
              {[copy.allServices.en, ...categories].map((x) => (
                <button
                  className={category === x ? "selected" : ""}
                  onClick={() => setCategory(x)}
                  key={x}
                >
                  {x === copy.allServices.en ? t.allServices : localize(categoryLabels[x])}
                </button>
              ))}
            </div>
            {filtered.length ? (
              <ServiceGrid services={filtered} />
            ) : (
              <div className="empty-state">
                <Search size={28} />
                <h3> {t.noServicesFound} </h3>
                <p> {t.tryAnotherSearchOrClearTheCategoryFilter} </p>
                <button
                  onClick={() => {
                    setQuery("");
                    setCategory(copy.allServices.en);
                  }}
                > {t.clearFilters} </button>
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
