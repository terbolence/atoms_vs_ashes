import pandas as pd
import pytest

from atoms_vs_ashes.gui.regional.helpers import (
    composite_quartile,
    quartile_rgb,
    truncate_site_label,
)


def test_truncate_site_label_short_unchanged():
    assert truncate_site_label("Short") == "Short"


def test_truncate_site_label_long():
    s = "A" * 50
    out = truncate_site_label(s, max_len=10)
    assert len(out) == 10
    assert out.endswith("…")


def test_quartile_rgb_negative_is_grey():
    assert quartile_rgb(-1) == (150, 150, 150)


@pytest.mark.parametrize("q", [0, 1, 2, 3])
def test_quartile_rgb_defined(q: int):
    assert len(quartile_rgb(q)) == 3


def test_composite_quartile_all_nan():
    s = pd.Series([None, None], dtype=object)
    out = composite_quartile(s)
    assert (out == -1).all()


def test_composite_quartile_small_sample():
    s = pd.Series([1.0, 2.0, 3.0])
    out = composite_quartile(s)
    assert (out >= 0).all()


def test_composite_quartile_many_values():
    s = pd.Series([float(i) for i in range(20)])
    out = composite_quartile(s)
    assert out.max() <= 3
    assert out.min() >= 0
