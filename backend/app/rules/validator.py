"""The validator: every travel rule as a check with an ID.  (Person A)

PHASE 0 STUB: returns no violations. Replace with the checks in rules/checks/*.
"""

from app.core.package_model import Package, Violation


def validate(pkg: Package) -> list[Violation]:
    """Empty list = the package is valid. Used by build, every change, confirm and export."""
    return []
