# Algorithm

We use a simple, transparent rule-based scoring:

- Candidate generation from seed genres/authors (or trending fallback)
- Score = 1.0×genre_overlap + 0.25×author_overlap + 0.10×popularity
- Popularity derived from recent stock_out transactions (normalized 0..1)
- Optional filter-out-of-stock and TTL cache
