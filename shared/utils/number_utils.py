import re
from typing import Optional, Union

# Regular expression to capture the first numeric token in the text. It supports
# optional sign, thousands separators and decimal separators using either a dot
# or a comma.
_NUMERIC_RE = re.compile(r"-?\d+(?:[\.,]\d+)?")


def extract_numeric(text: str) -> Optional[str]:
    """Return the first numeric substring found in *text*.

    The function normalises the decimal separator to a dot (".") and removes
    thousands separators when unambiguous. If no numeric token is present the
    function returns ``None``.
    """
    if not text:
        return None

    match = _NUMERIC_RE.search(text)
    if not match:
        return None

    token = match.group(0)

    # Heuristic normalisation rules:
    #   1. If there is exactly one comma and no dot -> treat comma as decimal.
    #   2. Otherwise strip all commas (assume they are thousands sep.)
    if token.count(".") == 0 and token.count(",") == 1:
        token = token.replace(",", ".")
    else:
        token = token.replace(",", "")

    return token


def safe_cast_to_float(value: Union[str, int, float]) -> Optional[float]:
    """Attempt to cast *value* to ``float`` in a permissive way.

    The function accepts various textual representations such as "10 dólares"
    or "$1,200.50" and returns the corresponding floating-point number.  If no
    numeric value can be inferred, ``None`` is returned.
    """

    # Fast-path for numerical types
    if isinstance(value, (int, float)):
        return float(value)

    numeric_str = extract_numeric(str(value))
    if numeric_str is None:
        return None

    try:
        return float(numeric_str)
    except ValueError:
        return None 