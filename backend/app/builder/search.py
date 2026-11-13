"""Package search: enumerate city plans, fill greedily, validate, choose by the city rule.  (Person A)

PHASE 0 STUB: `build` and `rebuild` have their final signatures but return the Menon fixture.
Replace the bodies; never change the signatures without telling Person B.
"""

from app.core.package_model import BuildResult, CityPlanSummary, CityStay, TripRequest
from app.stubs import menon_package


def build(req: TripRequest, mode: str = "default", strategy: str = "fast") -> BuildResult:
    """Build a package for a validated request.

    mode:     "default" = one package by the city rule; "three" = also fill `alternatives` (G4).
    strategy: "fast" (default) or "brute" (test oracle).
    """
    pkg = menon_package()
    pkg.budget_inr = req.budget_inr
    alternatives = {}
    if mode == "three":
        alternatives = {"cheapest": menon_package(), "fastest": menon_package(), "best_rated": menon_package()}
    return BuildResult(
        outcome="PACKAGE",
        package=pkg,
        alternatives=alternatives,
        city_plans=[CityPlanSummary(plan=list(pkg.city_plan), total_inr=pkg.total_inr, valid=True)],
    )


def rebuild(req: TripRequest, city_plan: list[CityStay]) -> BuildResult:
    """Build on one given city plan (G3)."""
    return build(req)
