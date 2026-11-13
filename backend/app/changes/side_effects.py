"""Apply a change and its knock-on effects (M6, G1).  (Person A)

PHASE 0 STUB: only `remove_attraction` changes the package; other changes return it unchanged.
The result is NOT validated here: changes/apply.py (Person B) calls validate() on it.
"""

import copy

from app.core.package_model import Change, ChangeResult, Package


def apply_change(pkg: Package, change: Change) -> ChangeResult:
    new = copy.deepcopy(pkg)
    if change.type == "remove_attraction":
        new.items = [i for i in new.items if not (i.item_id == change.item_id and i.type == "attraction")]
        return ChangeResult(package=new, side_effects=[], warnings=[])
    return ChangeResult(package=new, side_effects=[f"(stub) {change.type} change not applied yet"], warnings=[])
