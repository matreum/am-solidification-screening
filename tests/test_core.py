"""Unit tests for matreum_am_screening.core.

Tests cracking indices with synthetic solidification curves where the
expected behavior is known analytically.
"""

import numpy as np
import pytest

from matreum_am_screening.core import kou_index, clyne_davies, rdg_index


# ---------------------------------------------------------------------------
# Fixtures: synthetic solidification curves
# ---------------------------------------------------------------------------

@pytest.fixture
def linear_curve():
    """Linear T vs f_s: T = 1500 - 200*f_s (°C)."""
    f_s = np.linspace(0, 1, 1000)
    T = 1500.0 - 200.0 * f_s
    return T, f_s


@pytest.fixture
def steep_terminal_curve():
    """Curve with steep terminal solidification (high cracking risk).
    Gentle slope from f_s=0 to 0.85, then steep drop."""
    f_s = np.linspace(0, 1, 1000)
    T = np.where(
        f_s < 0.85,
        1500.0 - 50.0 * f_s,
        1500.0 - 50.0 * 0.85 - 600.0 * (f_s - 0.85),
    )
    return T, f_s


@pytest.fixture
def gentle_terminal_curve():
    """Curve with gentle terminal solidification (low cracking risk).
    Steep early, gentle at end."""
    f_s = np.linspace(0, 1, 1000)
    T = np.where(
        f_s < 0.5,
        1500.0 - 300.0 * f_s,
        1500.0 - 300.0 * 0.5 - 20.0 * (f_s - 0.5),
    )
    return T, f_s


# ---------------------------------------------------------------------------
# Kou index tests
# ---------------------------------------------------------------------------

class TestKouIndex:
    def test_positive_result(self, linear_curve):
        T, f_s = linear_curve
        result = kou_index(T, f_s)
        assert result > 0

    def test_steep_terminal_higher(self, steep_terminal_curve, gentle_terminal_curve):
        """Steep terminal solidification should give higher Kou index."""
        T_steep, fs_steep = steep_terminal_curve
        T_gentle, fs_gentle = gentle_terminal_curve
        kou_steep = kou_index(T_steep, fs_steep)
        kou_gentle = kou_index(T_gentle, fs_gentle)
        assert kou_steep > kou_gentle

    def test_insufficient_data(self):
        """Very short arrays should return 0."""
        T = np.array([1500.0, 1400.0])
        f_s = np.array([0.0, 1.0])
        assert kou_index(T, f_s) == 0.0


# ---------------------------------------------------------------------------
# Clyne-Davies tests
# ---------------------------------------------------------------------------

class TestClyneDavies:
    def test_linear_curve(self, linear_curve):
        """For a linear curve, the ratio is (T90-T99)/(T40-T90) = (200*0.09)/(200*0.50)."""
        T, f_s = linear_curve
        result = clyne_davies(T, f_s)
        expected = 0.09 / 0.50  # = 0.18
        assert abs(result - expected) < 0.01

    def test_positive(self, steep_terminal_curve):
        T, f_s = steep_terminal_curve
        result = clyne_davies(T, f_s)
        assert result > 0

    def test_steep_terminal_higher(self, steep_terminal_curve, gentle_terminal_curve):
        """Steep terminal should have higher CD ratio (more time in vulnerable zone)."""
        cd_steep = clyne_davies(*steep_terminal_curve)
        cd_gentle = clyne_davies(*gentle_terminal_curve)
        assert cd_steep > cd_gentle


# ---------------------------------------------------------------------------
# RDG index tests
# ---------------------------------------------------------------------------

class TestRDGIndex:
    def test_positive_result(self, linear_curve):
        T, f_s = linear_curve
        result = rdg_index(T, f_s)
        assert result > 0

    def test_gentle_terminal_higher_rdg(self, steep_terminal_curve, gentle_terminal_curve):
        """Gentle terminal slope → smaller |dT/df_s| in 0.90-0.99 range →
        higher RDG integrand (inverse proportionality). A shallow thermal
        gradient in the critical zone produces greater feeding resistance."""
        rdg_steep = rdg_index(*steep_terminal_curve)
        rdg_gentle = rdg_index(*gentle_terminal_curve)
        assert rdg_gentle > rdg_steep

    def test_insufficient_data(self):
        T = np.array([1500.0, 1400.0])
        f_s = np.array([0.0, 1.0])
        assert rdg_index(T, f_s) == 0.0
