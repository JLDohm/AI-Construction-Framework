"""Tests of the bldg library: units and geometry."""

import pytest

from bldg.geometry import Pt, is_axis_rect, polygon_area, rect, spaced_positions
from bldg.units import fmt_ft_in, fmt_in, ft, to_cuyd, to_sqft


def test_ft_converts_feet_and_inches() -> None:
    assert ft(7, 6) == 90.0
    assert ft(0, 3.5) == 3.5


def test_fmt_in_uses_builder_fractions() -> None:
    assert fmt_in(7.75) == '7 3/4"'
    assert fmt_in(0.375) == '3/8"'
    assert fmt_in(36) == '36"'
    assert fmt_in(9.25) == '9 1/4"'


def test_fmt_ft_in_rounds_to_sixteenths() -> None:
    assert fmt_ft_in(147.5) == "12'-3 1/2\""
    assert fmt_ft_in(144) == "12'-0\""
    assert fmt_ft_in(143.99) == "12'-0\""  # rounds up to the next whole foot


def test_area_and_volume_units() -> None:
    assert to_sqft(144 * 70) == 70
    assert to_cuyd(36**3) == 1


def test_polygon_area_of_rectangle_and_l_shape() -> None:
    assert polygon_area(rect(0, 0, ft(10), ft(12))) == ft(10) * ft(12)
    ell = [Pt(0, 0), Pt(20, 0), Pt(20, 10), Pt(10, 10), Pt(10, 20), Pt(0, 20)]
    assert polygon_area(ell) == 300


def test_rect_refuses_zero_size() -> None:
    with pytest.raises(ValueError):
        rect(0, 0, 0, 10)


def test_is_axis_rect() -> None:
    assert is_axis_rect(rect(5, 5, 10, 20))
    assert not is_axis_rect([Pt(0, 0), Pt(10, 0), Pt(12, 10), Pt(0, 10)])


def test_spaced_positions_include_both_ends() -> None:
    assert spaced_positions(40, 16) == [0, 16, 32, 40]
    assert spaced_positions(32, 16) == [0, 16, 32]
    with pytest.raises(ValueError):
        spaced_positions(40, 0)
