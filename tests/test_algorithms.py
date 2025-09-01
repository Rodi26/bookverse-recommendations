from app.schemas import BookLite, Availability
from app.algorithms import score_simple


def make_book(id_: str, genres, authors, in_stock=True):
    return BookLite(
        id=id_,
        title=f"Book {id_}",
        authors=list(authors),
        genres=list(genres),
        price=10.0,
        cover_image_url="",
        availability=Availability(quantity_available=1 if in_stock else 0, in_stock=in_stock, low_stock=False),
    )


def test_score_simple_prefers_genre_and_author_overlap():
    seed = make_book("s1", {"Fiction", "Mystery"}, {"Alice"})
    candidate1 = make_book("c1", {"Fiction", "Mystery"}, {"Alice"})
    candidate2 = make_book("c2", {"Fiction"}, {"Bob"})
    pop = {"c1": 0.1, "c2": 0.9}

    s1, _ = score_simple([seed], candidate1, pop)
    s2, _ = score_simple([seed], candidate2, pop)

    assert s1 > s2


def test_score_simple_filters_out_of_stock_when_enabled():
    seed = make_book("s1", {"Fiction"}, {"Alice"})
    candidate = make_book("c1", {"Fiction"}, {"Alice"}, in_stock=False)
    s, _ = score_simple([seed], candidate, {})
    assert s == 0.0


