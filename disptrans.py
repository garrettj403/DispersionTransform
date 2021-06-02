"""Dispersion-compensated algorithm for mapping dispersive waveguide data from
the frequency-domain to distance-domain, and vice versa."""

import numba as nb
import numpy as np


@nb.njit
def freq2distance(f, fresp, beta, x):
    """Transform a frequency-domain signal to the distance-domain.
    
    Compensates for dispersion.
    
    Args:
        f (np.ndarray): frequency for frequency-domain signal, in units [Hz]
        fresp (np.ndarray): frequency-domain signal
        beta (np.ndarray): phase constant, in units [rad/m]
        x (np.ndarray): distance array for output data, in units [m]
        
    Returns:
        np.ndarray: distance-domain response
        
    """

    # TODO: add default value for x

    fpts = len(f)  # number of frequency-domain points
    xpts = len(x)  # number of distance-domain points
    
    # Calculate distance-domain response, xresp
    # TODO: optimize
    xresp = np.zeros(xpts, dtype=np.complex128)
    for x_idx in range(xpts):
        xresp[x_idx] = np.sum(fresp * np.exp(1j * beta * x[x_idx]))

    # Normalize
    xresp /= fpts
    
    return xresp


@nb.njit
def distance2freq(x, xresp, beta, f):
    """Transform a distance-domain signal to the frequency-domain.
    
    Compensates for dispersion.
    
    Args:
        x (np.ndarray): distance array for input data, in units [m]
        xresp (np.ndarray): distance-domain response
        beta (np.ndarray): phase constant, in units [rad/m]
        f (np.ndarray): frequency for frequency-domain response, in units [Hz]
        
    Returns:
        np.ndarray: frequency-domain response
        
    """

    # TODO: add default value for f

    def _delta(xx):
        """Calculate derivative of xx."""
        result = np.zeros_like(xx)
        result[1:-1] = xx[2:] - xx[:-2]
        result[0] = result[1]
        result[-1] = result[-2]
        return result / 2

    fpts = len(f)  # number of frequency-domain points
    xstep = x[1] - x[0]  # distance-domain step size
    
    # Calculate frequency-domain response, fresp
    # TODO: optimize
    fresp = np.zeros(fpts, dtype=np.complex128)
    for f_idx in range(fpts):
        fresp[f_idx] = np.sum(xresp * np.exp(-1j * beta[f_idx] * x))
    
    # Group velocity
    vg = _delta(beta)

    # Normalize
    fresp *= fpts * xstep * vg / 2 / np.pi
    
    return fresp
