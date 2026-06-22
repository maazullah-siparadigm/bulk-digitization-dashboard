"""Pure, DB-independent histogram binning for token distributions.

Kept free of SQLAlchemy/ORM imports so the binning logic is unit-testable
in isolation.
"""

from bisect import bisect_right
from math import ceil

TOKEN_TYPES = ("input_tokens", "output_tokens", "thinking_tokens")
DEFAULT_NUM_BINS = 100


def _bin_edges(group_max: int, num_bins: int) -> list[int]:
    """Return num_bins+1 ascending edges spanning 0..group_max.

    The final edge is bumped past group_max when group_max sits exactly on a
    bin boundary, so the (exclusive-upper) top bin still includes the max.
    """
    if group_max <= 0:
        # Degenerate group: a single [0, 1) bin by design; num_bins is ignored.
        return [0, 1]
    width = ceil(group_max / num_bins)
    edges = [i * width for i in range(num_bins + 1)]
    if edges[-1] <= group_max:
        edges[-1] = group_max + 1
    return edges


def build_group_histograms(
    values_by_type: dict[str, list[int]], num_bins: int = DEFAULT_NUM_BINS
) -> dict[str, list[dict]]:
    """Bin each token-type list into buckets that share one set of edges.

    values_by_type maps token-type name -> list of per-response counts.
    Returns {token_type: [{"bin_start", "bin_end", "count"}, ...]} for every
    token type in TOKEN_TYPES (empty types still get the shared bins).
    """
    all_values = [v for tt in TOKEN_TYPES for v in values_by_type.get(tt, [])]
    group_max = max(all_values) if all_values else 0
    edges = _bin_edges(group_max, num_bins)
    num_actual = len(edges) - 1

    result = {}
    for tt in TOKEN_TYPES:
        counts = [0] * num_actual
        for v in values_by_type.get(tt, []):
            idx = bisect_right(edges, v) - 1
            if idx < 0:
                idx = 0
            elif idx >= num_actual:
                idx = num_actual - 1
            counts[idx] += 1
        result[tt] = [
            {"bin_start": edges[i], "bin_end": edges[i + 1], "count": counts[i]}
            for i in range(num_actual)
        ]
    return result
