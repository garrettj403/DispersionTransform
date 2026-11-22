"""Test the dispersion-compensated algorithm package."""

import numpy as np
import pytest
import scipy.constants as sc

# SciKit-RF: https://scikit-rf.readthedocs.io/
from skrf.frequency import Frequency
from skrf.media import RectangularWaveguide

import disptrans

# WR-2.8 waveguide dimensions
A, B, LENGTH = 28 * sc.mil, 14 * sc.mil, 2 * sc.inch

# Points far enough from the band edges to avoid edge effects
BAND = (265e9, 395e9)


def make_waveguide(rho=None, length=LENGTH):
    """Return f, beta and S21 for a WR-2.8 waveguide section.

    rho=None gives a lossless waveguide. (rho must always be passed
    explicitly: scikit-rf >= 1.0 defaults to copper walls.)

    """
    freq = Frequency(260, 400, 1401, 'ghz')
    wr2p8 = RectangularWaveguide(freq.copy(), a=A, b=B, rho=rho)
    beta = wr2p8.beta.copy()
    waveguide = wr2p8.line(length, unit='m')
    return freq.f.copy(), beta, waveguide.s[:, 1, 0].copy()


def roundtrip(f, beta, s21f):
    """Frequency -> distance -> frequency, with a Hamming window."""
    x = np.linspace(-LENGTH * 10, LENGTH * 12, 1401)
    s21x = disptrans.freq2distance(f, s21f, beta, x)
    return disptrans.distance2freq(x, s21x * np.hamming(len(x)), beta, f)


# Round trip ------------------------------------------------------------------

@pytest.mark.parametrize("rho", [None, "au"], ids=["lossless", "lossy"])
def test_roundtrip(rho):
    """Frequency -> distance -> frequency recovers the original response."""
    f, beta, s21f = make_waveguide(rho)
    fresp = roundtrip(f, beta, s21f)
    mask = (BAND[0] < f) & (f < BAND[1])
    np.testing.assert_almost_equal(s21f[mask], fresp[mask], decimal=3)


def test_lossless_single_point():
    """Lossless line has unity response at its own length."""
    f, beta, s21f = make_waveguide()
    s21x = disptrans.freq2distance(f, s21f, beta, np.array([LENGTH]))
    np.testing.assert_almost_equal(np.ones(1), s21x, decimal=3)


def test_matches_reference_implementation():
    """Numba kernels match a direct NumPy implementation."""
    f, beta, s21f = make_waveguide("au")
    x = np.linspace(-0.1, 0.2, 301)
    expected = (s21f[None, :] * np.exp(1j * np.outer(x, beta))).sum(axis=1) / len(f)
    np.testing.assert_allclose(disptrans.freq2distance(f, s21f, beta, x), expected, atol=1e-12)

    xresp = expected * np.hamming(len(x))
    dbeta = np.gradient(beta)
    expected_f = (xresp[None, :] * np.exp(-1j * np.outer(beta, x))).sum(axis=1)
    expected_f *= len(f) * (x[1] - x[0]) * dbeta / (2 * np.pi)
    np.testing.assert_allclose(disptrans.distance2freq(x, xresp, beta, f), expected_f, atol=1e-12)


def test_accepts_lists_and_ints():
    """Inputs are cast to the right dtypes."""
    f, beta, s21f = make_waveguide()
    out = disptrans.freq2distance(list(f), list(s21f), list(beta), [0, 1])
    assert out.dtype == np.complex128 and out.shape == (2,)


def test_complex_beta_with_zero_imag_is_accepted():
    f, beta, s21f = make_waveguide()
    a = disptrans.freq2distance(f, s21f, beta, [LENGTH])
    b = disptrans.freq2distance(f, s21f, beta + 0j, [LENGTH])
    np.testing.assert_allclose(a, b)


def test_two_point_beta():
    """Two frequency points works (previously returned all zeros)."""
    f, beta, s21f = make_waveguide()
    x = np.linspace(0, 0.1, 11)
    out = disptrans.distance2freq(x, np.ones(len(x)), beta[:2], f[:2])
    assert np.all(out != 0)


# Defaults --------------------------------------------------------------------

def test_default_distance_finds_peak():
    """With the default distance array, the peak is at the line length."""
    f, beta, s21f = make_waveguide()
    x = disptrans.default_distance(beta)
    assert len(x) == len(f) and x[0] == 0
    s21x = disptrans.freq2distance(f, s21f, beta)
    assert abs(x[np.abs(s21x).argmax()] - LENGTH) < 2 * (x[1] - x[0])


def test_default_distance_npts():
    _, beta, _ = make_waveguide()
    assert len(disptrans.default_distance(beta, npts=10)) == 10


# Gating ----------------------------------------------------------------------

def test_gate():
    x = np.linspace(0, 10, 101)
    xresp = np.ones(len(x))
    gated = disptrans.gate(x, xresp, center=5, half_width=1)
    inside = (x >= 4) & (x <= 6)
    np.testing.assert_allclose(gated[~inside], 0)
    np.testing.assert_allclose(gated[inside], np.hamming(inside.sum()))


def test_gate_callable_and_boxcar():
    x = np.linspace(0, 10, 101)
    xresp = np.arange(len(x)) + 0j
    a = disptrans.gate(x, xresp, 5, 1, window="boxcar")
    b = disptrans.gate(x, xresp, 5, 1, window=np.ones)
    np.testing.assert_allclose(a, b)


@pytest.mark.parametrize("kwargs", [
    dict(window="nope"),
    dict(half_width=0),
    dict(center=100),
])
def test_gate_errors(kwargs):
    x = np.linspace(0, 10, 101)
    args = dict(center=5, half_width=1)
    args.update(kwargs)
    with pytest.raises(ValueError):
        disptrans.gate(x, np.ones(len(x)), **args)


# Input validation ------------------------------------------------------------

def test_distance2freq_single_x_point_raises():
    """Previously read past the end of x and returned garbage."""
    f, beta, _ = make_waveguide()
    with pytest.raises(ValueError, match="at least 2"):
        disptrans.distance2freq(np.array([0.05]), np.array([1 + 0j]), beta, f)


def test_distance2freq_nonuniform_x_raises():
    """Previously returned a silently wrong result."""
    f, beta, _ = make_waveguide()
    x = np.sort(np.random.default_rng(0).uniform(-0.5, 0.6, 101))
    with pytest.raises(ValueError, match="uniformly spaced"):
        disptrans.distance2freq(x, np.ones(len(x)), beta, f)


def test_mismatched_lengths_raise():
    f, beta, s21f = make_waveguide()
    with pytest.raises(ValueError, match="fresp and f"):
        disptrans.freq2distance(f, s21f[:10], beta, [0.0])
    with pytest.raises(ValueError, match="f and beta"):
        disptrans.freq2distance(f[:10], s21f[:10], beta, [0.0])
    with pytest.raises(ValueError, match="xresp and x"):
        disptrans.distance2freq([0, 1, 2], [1, 2], beta, f)


def test_complex_beta_raises():
    f, beta, s21f = make_waveguide()
    with pytest.raises(ValueError, match="must be real"):
        disptrans.freq2distance(f, s21f, beta + 1j, [0.0])


def test_nonmonotonic_beta_raises():
    f, beta, s21f = make_waveguide()
    beta = beta.copy()
    beta[10] = beta[9]
    with pytest.raises(ValueError, match="monotonic"):
        disptrans.freq2distance(f, s21f, beta, [0.0])


def test_nonfinite_input_raises():
    f, beta, s21f = make_waveguide()
    s21f = s21f.copy()
    s21f[0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        disptrans.freq2distance(f, s21f, beta, [0.0])


# Manual check ----------------------------------------------------------------

def plot_roundtrip(rho=None):
    """Plot original vs. recovered response (for manual inspection)."""
    import matplotlib.pyplot as plt

    f, beta, s21f = make_waveguide(rho)
    fresp = roundtrip(f, beta, s21f)
    mask = (BAND[0] < f) & (f < BAND[1])

    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
    ax1.plot(f[mask] / 1e9, db20(s21f[mask]), 'k--', label="Original")
    ax1.plot(f[mask] / 1e9, db20(fresp[mask]), 'r', alpha=0.5, label="Recovered")
    ax1.set_ylabel("S21 magnitude (dB)")
    ax1.legend()
    ax2.plot(f[mask] / 1e9, unwrap(s21f[mask]), 'k--')
    ax2.plot(f[mask] / 1e9, unwrap(fresp[mask]), 'r', alpha=0.5)
    ax2.set_ylabel("S21 phase (deg)")
    ax2.set_xlabel("Frequency (GHz)")
    fig.suptitle("lossless" if rho is None else "rho={}".format(rho))


def db20(value):
    """Return voltage-like value in dB."""
    return 20 * np.log10(np.abs(value))


def unwrap(value):
    """Unwrap phase."""
    return 180 / np.pi * np.unwrap(np.angle(value))


if __name__ == "__main__":

    import matplotlib.pyplot as plt

    plot_roundtrip()
    plot_roundtrip("au")
    plt.show()
