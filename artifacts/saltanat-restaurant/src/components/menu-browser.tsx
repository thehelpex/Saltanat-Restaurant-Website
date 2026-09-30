"use client";

import { useListRestaurantMenu } from "@workspace/api-client-react";
import { getListRestaurantMenuQueryKey } from "@workspace/api-client-react";
import { Search, RotateCw, UtensilsCrossed } from "lucide-react";
import { useMemo, useState } from "react";

const categories = ["All", "Starters", "Soup & Salad", "BBQ & Grills", "Karahi & Handi", "Tawa Specials", "Seafood", "Family Platters", "Burgers", "Desserts & Drinks"];
const formatPrice = (amount: number) => new Intl.NumberFormat("en-PK", { maximumFractionDigits: 0 }).format(amount);

export function MenuBrowser() {
  const [category, setCategory] = useState("All");
  const [search, setSearch] = useState("");
  const params = useMemo(() => ({ category: category === "All" ? undefined : category, search: search.trim() || undefined }), [category, search]);
  const menu = useListRestaurantMenu(params, { query: { queryKey: getListRestaurantMenuQueryKey(params) } });
  return (
    <section className="page-content">
      <div className="wrap">
        <div className="menu-controls">
          <div className="eyebrow">A menu to meet in the middle</div>
          <label className="search-box"><Search size={17} aria-hidden="true" /><span className="sr-only">Search menu</span><input data-testid="input-menu-search" type="search" placeholder="Search dishes" value={search} onChange={(event) => setSearch(event.target.value)} /></label>
        </div>
        <div className="category-list" role="group" aria-label="Filter menu by category">
          {categories.map((item) => <button className={`category-chip${category === item ? " active" : ""}`} type="button" key={item} aria-pressed={category === item} onClick={() => setCategory(item)}>{item}</button>)}
        </div>
        <p className="notice">Prices are in PKR and may change. Please check with the restaurant for current availability.</p>
        {menu.isLoading ? <div className="loading-block" aria-label="Loading menu">{Array.from({ length: 6 }, (_, index) => <div className="skeleton" key={index} />)}</div> :
          menu.isError ? <div className="error-panel" role="alert"><h2>We could not load the menu.</h2><p>Please try again in a moment.</p><button type="button" className="button button-outline" onClick={() => menu.refetch()}><RotateCw size={14} /> Retry menu</button></div> :
          menu.data?.length ? <div className="menu-grid" aria-live="polite">
            {menu.data.map((item) => <article className="menu-item" key={item.id} data-testid={`menu-item-${item.id}`}>
              {item.imageUrl ? <img className="menu-image" src={item.imageUrl} alt="" loading="lazy" /> : <div className="menu-image menu-image-placeholder" aria-hidden="true"><UtensilsCrossed size={19} /></div>}
              <div className="menu-item-info"><p className="menu-category">{item.category}{item.isFeatured ? " · Featured" : ""}</p><h3>{item.name}</h3>{item.description && <p>{item.description}</p>}</div>
              <span className="menu-price">PKR {formatPrice(item.pricePkr)}</span>
            </article>)}
          </div> :
          <div className="empty-panel" aria-live="polite"><h2>No dishes found just yet.</h2><p>Try another search or browse all categories.</p><button className="button button-outline" type="button" onClick={() => { setSearch(""); setCategory("All"); }}>Show all dishes</button></div>}
      </div>
    </section>
  );
}