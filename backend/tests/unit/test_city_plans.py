"""City plan enumeration and the city rule."""

from app.builder.city_plans import compositions, enumerate_plans, target_city_count
from app.builder.selector import city_count_order

JAPAN = ["Tokyo", "Kyoto", "Osaka"]
ALL_LINKS = {(a, b) for a in JAPAN for b in JAPAN if a != b}


def test_compositions():
    assert compositions(6, 2, 2) == [(2, 4), (3, 3), (4, 2)]
    assert compositions(5, 3, 2) == []
    assert len(compositions(10, 3, 2)) == 15


def test_japan_10_nights_has_135_plans():
    assert len(enumerate_plans(JAPAN, 10, 2, ALL_LINKS)) == 135


def test_every_plan_respects_d3():
    for plan in enumerate_plans(JAPAN, 7, 2, ALL_LINKS):
        assert sum(c.nights for c in plan) == 7
        assert all(c.nights >= 2 for c in plan)
        assert len({c.city for c in plan}) == len(plan)


def test_links_and_airport_ends_filter_plans():
    plans = enumerate_plans(JAPAN, 6, 2, {("Tokyo", "Kyoto")}, first_ok={"Tokyo"}, last_ok={"Kyoto", "Osaka"})
    assert {tuple(c.city for c in p) for p in plans} == {("Tokyo", "Kyoto")}


def test_city_rule_target():
    assert target_city_count(6, 3) == 2          # Menon
    assert target_city_count(9, 3) == 3
    assert target_city_count(9, 2) == 2          # UAE cap
    assert target_city_count(3, 3) == 1
    assert target_city_count(5, 3) == 1


def test_city_count_order():
    assert city_count_order(2, 3) == [2, 1, 3]
    assert city_count_order(1, 2) == [1, 2]
