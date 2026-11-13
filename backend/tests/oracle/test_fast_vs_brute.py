"""Safety net: the fast search must give the same answer as the exhaustive one on every fixture request.

`brute` tries every (arrival flight, transfer, first hotel) × (return flight, transfer, last hotel)
combination per city plan, so if a future speed-up misses a cheaper package, this test fails.
"""

import pytest

from app.builder.search import build
from tests.helpers import request_fixtures, to_request

CASES = request_fixtures()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_fast_equals_brute(case, catalog_store):
    req = to_request(case["request"])
    fast, brute = build(req), build(req, strategy="brute")
    assert fast.outcome == brute.outcome
    assert [(tuple((c.city, c.nights) for c in s.plan), s.total_inr) for s in fast.city_plans] == \
           [(tuple((c.city, c.nights) for c in s.plan), s.total_inr) for s in brute.city_plans]
    if fast.package:
        assert fast.package.total_inr == brute.package.total_inr
