"""Integer INR money helpers and formatting with Indian number grouping."""

from __future__ import annotations


def format_inr(amount: int) -> str:
    """Format an integer INR amount with Indian number grouping and rupee symbol.

    Examples:
        0          -> "₹0"
        500        -> "₹500"
        1234       -> "₹1,234"
        234710     -> "₹2,34,710"
        350000     -> "₹3,50,000"
        10000000   -> "₹1,00,00,000"
        -5000      -> "-₹5,000"
    """
    is_negative = amount < 0
    num_str = str(abs(amount))

    if len(num_str) <= 3:
        formatted = num_str
    else:
        last3 = num_str[-3:]
        rest = num_str[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted = ",".join(groups) + "," + last3

    return f"-₹{formatted}" if is_negative else f"₹{formatted}"
