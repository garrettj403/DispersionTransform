"""Dispersion-compensated algorithm for mapping dispersive waveguide data from
the frequency-domain to distance-domain, and vice versa.

Reference:

    J. D. Garrett and C. E. Tong, "A Dispersion-Compensated Algorithm for the
    Analysis of Electromagnetic Waveguides," IEEE Signal Processing Letters,
    vol. 28, pp. 1175-1179, 2021, doi: 10.1109/LSP.2021.3086695.

"""

import numba as nb
import numpy as np

__version__ = "0.1.0"

__all__ = ["freq2distance", "distance2freq", "default_distance", "gate"]

_WINDOWS = {
    "boxcar": np.ones,
    "rect": np.ones,
    "hamming": np.hamming,
    "hann": np.hanning,
    "hanning": np.hanning,
    "blackman": np.blackman,
    "bartlett": np.bartlett,
}


# Public API ------------------------------------------------------------------

def freq2distance(f, fresp, beta, x=None):
    """Transform a frequency-domain signal to the distance-domain.

    Compensates for dispersion.

    Args:
        f (np.ndarray): frequency for frequency-domain signal, in units [Hz]
        fresp (np.ndarray): frequency-domain signal
        beta (np.ndarray): phase constant, in units [rad/m]. Must be real and
            strictly monotonic (i.e., all points above cutoff).
        x (np.ndarray, optional): distance array for output data, in units
            [m]. Defaults to ``default_distance(beta)``.

    Returns:
        np.ndarray: distance-domain response

    """

    _, beta, fresp = _check_freq_inputs(f, beta, fresp=fresp)

    if x is None:
        x = default_distance(beta)
    x = _as_float_array(x, "x")
    if x.size == 0:
        raise ValueError("x must not be empty.")

    return _freq2distance(fresp, beta, x)


def distance2freq(x, xresp, beta, f):
    """Transform a distance-domain signal to the frequency-domain.

    Compensates for dispersion.

    The output frequency grid is defined by ``beta`` (one output point per
    value of ``beta``); ``f`` must be the matching frequency array.

    Args:
        x (np.ndarray): distance array for input data, in units [m]. Must be
            uniformly spaced, with at least 2 points.
        xresp (np.ndarray): distance-domain response
        beta (np.ndarray): phase constant, in units [rad/m]. Must be real and
            strictly monotonic (i.e., all points above cutoff).
        f (np.ndarray): frequency for frequency-domain response, in units [Hz]

    Returns:
        np.ndarray: frequency-domain response

    """

    _, beta, _ = _check_freq_inputs(f, beta)

    x = _as_float_array(x, "x")
    xresp = _as_complex_array(xresp, "xresp")
    if x.size < 2:
        raise ValueError("x must have at least 2 points.")
    if xresp.shape != x.shape:
        raise ValueError("xresp and x must have the same length "
                         "(got {} and {}).".format(xresp.size, x.size))
    xstep = _uniform_step(x)

    # Phase constant step at each frequency point, d(beta)/d(index). This is
    # the Jacobian that converts the sum over frequency points into an
    # integral over beta.
    dbeta = np.gradient(beta)

    fresp = _distance2freq(xresp, beta, x)
    fresp *= beta.size * xstep * dbeta / (2 * np.pi)

    return fresp


def default_distance(beta, npts=None):
    """Default distance array for the distance-domain response.

    Analogous to the time array of an IFFT: the step size is set by the
    total span of ``beta`` and the array covers one unambiguous range,
    ``2 * pi / mean(d_beta)``, starting at zero.

    Args:
        beta (np.ndarray): phase constant, in units [rad/m]
        npts (int, optional): number of points. Defaults to ``len(beta)``.

    Returns:
        np.ndarray: distance array, in units [m]

    """

    beta = _check_beta(beta)
    if npts is None:
        npts = beta.size
    npts = int(npts)
    if npts < 1:
        raise ValueError("npts must be at least 1.")
    mean_dbeta = np.abs(beta[-1] - beta[0]) / (beta.size - 1)
    return np.linspace(0, 2 * np.pi / mean_dbeta, npts, endpoint=False)


def gate(x, xresp, center, half_width, window="hamming"):
    """Isolate part of a distance-domain response using a window.

    Points outside of ``[center - half_width, center + half_width]`` are set
    to zero and the window is applied to the points inside.

    Args:
        x (np.ndarray): distance array, in units [m]. Must be sorted.
        xresp (np.ndarray): distance-domain response
        center (float): center of the gate, in units [m]
        half_width (float): half-width of the gate, in units [m]
        window (str or callable): window name ("hamming", "hann", "blackman",
            "bartlett" or "boxcar") or a function that takes the number of
            points and returns the window, e.g., ``scipy.signal.windows.tukey``
            wrapped in a lambda. Defaults to "hamming".

    Returns:
        np.ndarray: gated distance-domain response

    """

    x = _as_float_array(x, "x")
    xresp = _as_complex_array(xresp, "xresp")
    if xresp.shape != x.shape:
        raise ValueError("xresp and x must have the same length.")
    if np.any(np.diff(x) <= 0):
        raise ValueError("x must be strictly increasing.")
    if half_width <= 0:
        raise ValueError("half_width must be positive.")

    if callable(window):
        window_fn = window
    else:
        try:
            window_fn = _WINDOWS[window.lower()]
        except (KeyError, AttributeError):
            raise ValueError("Unknown window: {!r}. Choose from: {}.".format(
                window, ", ".join(sorted(_WINDOWS)))) from None

    mask = (x >= center - half_width) & (x <= center + half_width)
    npts = int(mask.sum())
    if npts == 0:
        raise ValueError("Gate does not contain any points of x.")

    win = np.zeros(x.size)
    win[mask] = np.asarray(window_fn(npts), dtype=float)

    return xresp * win


# Input validation ------------------------------------------------------------

def _as_float_array(value, name):
    arr = np.asarray(value)
    if arr.ndim != 1:
        raise ValueError("{} must be a 1D array.".format(name))
    if np.iscomplexobj(arr):
        raise ValueError("{} must be real.".format(name))
    arr = arr.astype(np.float64)
    if not np.all(np.isfinite(arr)):
        raise ValueError("{} must be finite.".format(name))
    return np.ascontiguousarray(arr)


def _as_complex_array(value, name):
    arr = np.asarray(value)
    if arr.ndim != 1:
        raise ValueError("{} must be a 1D array.".format(name))
    arr = arr.astype(np.complex128)
    if not np.all(np.isfinite(arr)):
        raise ValueError("{} must be finite.".format(name))
    return np.ascontiguousarray(arr)


def _check_beta(beta):
    beta = np.asarray(beta)
    if np.iscomplexobj(beta):
        if np.any(beta.imag != 0):
            raise ValueError("beta must be real (the phase constant, not the "
                             "complex propagation constant).")
        beta = beta.real
    beta = _as_float_array(beta, "beta")
    if beta.size < 2:
        raise ValueError("beta must have at least 2 points.")
    dbeta = np.diff(beta)
    if not (np.all(dbeta > 0) or np.all(dbeta < 0)):
        raise ValueError("beta must be strictly monotonic. Make sure all "
                         "frequency points are above the cutoff frequency.")
    return beta


def _check_freq_inputs(f, beta, fresp=None):
    f = _as_float_array(f, "f")
    beta = _check_beta(beta)
    if f.size != beta.size:
        raise ValueError("f and beta must have the same length "
                         "(got {} and {}).".format(f.size, beta.size))
    if fresp is not None:
        fresp = _as_complex_array(fresp, "fresp")
        if fresp.size != f.size:
            raise ValueError("fresp and f must have the same length "
                             "(got {} and {}).".format(fresp.size, f.size))
    return f, beta, fresp


def _uniform_step(x):
    steps = np.diff(x)
    step = steps.mean()
    if step <= 0 or not np.allclose(steps, step, rtol=1e-6, atol=0):
        raise ValueError("x must be uniformly spaced and increasing.")
    return step


# Numba kernels ---------------------------------------------------------------

@nb.njit(parallel=True, cache=True)
def _freq2distance(fresp, beta, x):
    """Kernel for freq2distance (inputs must already be validated)."""
    fpts = beta.size
    xresp = np.empty(x.size, dtype=np.complex128)
    for i in nb.prange(x.size):
        acc = 0j
        for k in range(fpts):
            acc += fresp[k] * np.exp(1j * beta[k] * x[i])
        xresp[i] = acc / fpts
    return xresp


@nb.njit(parallel=True, cache=True)
def _distance2freq(xresp, beta, x):
    """Kernel for distance2freq, without normalization."""
    fresp = np.empty(beta.size, dtype=np.complex128)
    for k in nb.prange(beta.size):
        acc = 0j
        for i in range(x.size):
            acc += xresp[i] * np.exp(-1j * beta[k] * x[i])
        fresp[k] = acc
    return fresp
