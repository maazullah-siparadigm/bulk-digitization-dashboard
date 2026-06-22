from histogram import build_group_histograms, TOKEN_TYPES, DEFAULT_NUM_BINS


def _edges(buckets):
    """Return the (bin_start, bin_end) edge pairs for one token-type's buckets."""
    return [(b["bin_start"], b["bin_end"]) for b in buckets]


def test_all_three_token_types_present_even_when_empty():
    result = build_group_histograms({"input_tokens": [], "output_tokens": [], "thinking_tokens": []})
    assert set(result.keys()) == set(TOKEN_TYPES)


def test_empty_group_yields_single_zero_bin():
    result = build_group_histograms({"input_tokens": [], "output_tokens": [], "thinking_tokens": []})
    for tt in TOKEN_TYPES:
        assert result[tt] == [{"bin_start": 0, "bin_end": 1, "count": 0}]


def test_all_zero_values_land_in_single_bin():
    result = build_group_histograms({"input_tokens": [0, 0, 0], "output_tokens": [0], "thinking_tokens": []})
    assert result["input_tokens"] == [{"bin_start": 0, "bin_end": 1, "count": 3}]
    assert result["output_tokens"] == [{"bin_start": 0, "bin_end": 1, "count": 1}]
    assert result["thinking_tokens"] == [{"bin_start": 0, "bin_end": 1, "count": 0}]


def test_shared_edges_across_token_types():
    # input drives the max (100); all three must use identical edges.
    values = {
        "input_tokens": [0, 50, 100],
        "output_tokens": [10],
        "thinking_tokens": [],
    }
    result = build_group_histograms(values, num_bins=DEFAULT_NUM_BINS)
    assert _edges(result["input_tokens"]) == _edges(result["output_tokens"]) == _edges(result["thinking_tokens"])


def test_bin_count_and_default_count():
    result = build_group_histograms({"input_tokens": [0, 50, 100], "output_tokens": [], "thinking_tokens": []})
    # 20 equal-width bins by default.
    assert len(result["input_tokens"]) == DEFAULT_NUM_BINS
    # width = ceil(100 / 20) = 5 -> edges 0,5,10,...,100 (top bumped to 101 to include max).
    assert result["input_tokens"][0]["bin_start"] == 0
    assert result["input_tokens"][0]["bin_end"] == 5


def test_lower_bound_inclusive_upper_exclusive():
    # value 5 with width 5 must fall in [5, 10), not [0, 5).
    result = build_group_histograms({"input_tokens": [5, 100], "output_tokens": [], "thinking_tokens": []})
    bins = result["input_tokens"]
    assert bins[0] == {"bin_start": 0, "bin_end": 5, "count": 0}
    assert bins[1]["bin_start"] == 5 and bins[1]["bin_end"] == 10 and bins[1]["count"] == 1


def test_group_max_lands_in_top_bin_when_max_is_bin_multiple():
    # max=100 is an exact multiple of width=5; top edge must extend so 100 is counted.
    result = build_group_histograms({"input_tokens": [100], "output_tokens": [], "thinking_tokens": []})
    bins = result["input_tokens"]
    assert sum(b["count"] for b in bins) == 1
    assert bins[-1]["count"] == 1
    assert bins[-1]["bin_end"] > 100


def test_bins_sorted_by_bin_start():
    result = build_group_histograms({"input_tokens": [0, 37, 81, 100], "output_tokens": [], "thinking_tokens": []})
    starts = [b["bin_start"] for b in result["input_tokens"]]
    assert starts == sorted(starts)
