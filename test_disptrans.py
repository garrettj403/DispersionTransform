"""Test the dispersion-compensated algorithm package."""

import numpy as np
import scipy.constants as sc

# SciKit-RF: https://scikit-rf.readthedocs.io/
from skrf.frequency import Frequency
from skrf.media import RectangularWaveguide

import disptrans


def test_lossless_waveguide(debug=False):
    """Test lossless WR-2.8 waveguide."""

    # Waveguide dimensions
    a, b, length = 28 * sc.mil, 14 * sc.mil, 2 * sc.inch

    # Full frequency sweep for WR-2.8
    freq = Frequency(260, 400, 1401, 'ghz')

    # Create an ideal WR-2.8 waveguide
    wr2p8 = RectangularWaveguide(freq.copy(), a=a, b=b)
    beta = wr2p8.beta.copy()  # phase constant

    # Create 2 inch long waveguide
    waveguide = wr2p8.line(length, unit='m')

    # Unpack
    f = freq.f.copy()
    s21f = waveguide.s[:, 1, 0].copy()

    # Calculate space-domain response: single point
    x = np.array([length])
    s21x = disptrans.freq2distance(f, s21f, beta, x)

    # Check distance-domain response
    if debug:
        print(s21x)
    else:
        np.testing.assert_almost_equal(np.ones(1), s21x, decimal=3)

    # Calculate space-domain response: sweep
    x = np.linspace(-length * 10, length * 12, 1401)
    s21x = disptrans.freq2distance(f, s21f, beta, x)

    # Go back to frequency-domain
    fresp = disptrans.distance2freq(x, s21x * np.hamming(len(x)), beta, f)

    # Truncate
    mask = (265e9 < f) & (f < 395e9)

    # Debug
    if debug:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(f[mask] / 1e9, unwrap(s21f[mask]), 'k--', label="Original")
        plt.plot(f[mask] / 1e9, unwrap(fresp[mask]), 'r', alpha=0.5, label="Recovered")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("S21 phase (deg)")
        plt.title("S21 phase")
        plt.legend()
        plt.figure()
        plt.plot(f[mask] / 1e9, db20(s21f[mask]), 'k--', label="Original")
        plt.plot(f[mask] / 1e9, db20(fresp[mask]), 'r', alpha=0.5, label="Recovered")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("S21 magnitude (dB)")
        plt.title("S21 magnitude")
        plt.legend()
        plt.show()

    # Check
    if not debug:
        np.testing.assert_almost_equal(s21f[mask], fresp[mask], decimal=3)


def test_lossy_waveguide(debug=False):
    """Test lossy WR-2.8 waveguide."""

    # Waveguide imensions
    a, b, length = 28*sc.mil, 14*sc.mil, 2*sc.inch

    # Full frequency sweep for WR-2.8 waveguide
    freq = Frequency(260, 400, 1401, 'ghz')

    # Create an ideal WR-2.8 waveguide
    wr2p8 = RectangularWaveguide(freq.copy(), a=a, b=b, rho="au")
    beta = wr2p8.beta.copy()  # phase constant

    # Create 2 inch long waveguide
    waveguide = wr2p8.line(length, unit='m')

    # Unpack
    f = freq.f.copy()
    s21f = waveguide.s[:, 1, 0].copy()

    # Calculate space-domain response
    x = np.linspace(-length*10, length*12, 1401)
    s21x = disptrans.freq2distance(f, s21f, beta, x)

    # Go back to frequency-domain
    fresp = disptrans.distance2freq(x, s21x*np.hamming(len(x)), beta, f)

    # Truncate
    mask = (265e9 < f) & (f < 395e9)

    # Debug
    if debug:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(f[mask] / 1e9, unwrap(s21f[mask]), 'k--', label="Original")
        plt.plot(f[mask] / 1e9, unwrap(fresp[mask]), 'r', alpha=0.5, label="Recovered")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("S21 phase (deg)")
        plt.title("S21 phase")
        plt.legend()
        plt.figure()
        plt.plot(f[mask] / 1e9, db20(s21f[mask]), 'k--', label="Original")
        plt.plot(f[mask] / 1e9, db20(fresp[mask]), 'r', alpha=0.5, label="Recovered")
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("S21 magnitude (dB)")
        plt.title("S21 magnitude")
        plt.legend()
        plt.show()

    # Check
    if not debug:
        np.testing.assert_almost_equal(s21f[mask], fresp[mask], decimal=3)


def db10(value):
    """Return power-like value in dB."""
    return 10 * np.log10(np.abs(value))


def db20(value):
    """Return voltage-like value in dB."""
    return 20 * np.log10(np.abs(value))


def unwrap(value):
    """Unwrap phase."""
    return 180 / np.pi * np.unwrap(np.angle(value))


if __name__ == "__main__":

    test_lossless_waveguide(debug=True)
    test_lossy_waveguide(debug=True)
