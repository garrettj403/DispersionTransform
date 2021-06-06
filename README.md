Dispersion-Compensated Algorithm
================================

*Dispersion-Compensated Algorithm for the Analysis for Electromagnetic Waveguides*

This package allows you to map dispersive waveguide data from the frequency-domain to distance-domain, and vice versa. The benefit of this approach, compared to a standard Fourier transform, is that this algorithm compensated for dispersion. Normally, this causes signals in the time-domain to broaden as the propagate, making it difficult to isolate or supress adjacent signals. In the distance-domain, the signals remain sharp, even over long distances.

For more information, see: 

   - J. D. Garrett and C. E. Tong, ["A Dispersion-Compensated Algorithm for the Analysis of Electromagnetic Waveguides",](https://ieeexplore.ieee.org/document/9447194) *IEEE Signal Processing Letters*, Jun. 2021, doi: [10.1109/LSP.2021.3086695](https://doi.org/10.1109/LSP.2021.3086695).

Example: Waveguide Cavity Resonator
-----------------------------------

This is a quick example showing the power of the dispersion-compensated algorithm. See [the notebook](https://github.com/garrettj403/DispersionTransform/blob/main/examples/example-waveguide-cavity.ipynb) for more information.

For this example, we will look at the frequency-domain of a waveguide cavity resonator, as shown below.

<img src="https://raw.githubusercontent.com/garrettj403/DispersionTransform/main/examples/results/cavity-distance-domain.jpg" width="500">

In the distance-domain, we can see a series of reflections corresponding to different signal paths within the resonator. (I.e., the first peak is the signal passing straight through the resonator, the second peak is the signal that undergoes ones internal back-and-forth reflection, etc.)

<img src="https://raw.githubusercontent.com/garrettj403/DispersionTransform/main/examples/results/cavity-distance-domain.jpg" width="500">

In the distance-domain, we can easily isolate the first peak and then return to the frequency-domain.

<img src="https://raw.githubusercontent.com/garrettj403/DispersionTransform/main/examples/results/cavity-peak1.jpg" width="500">

Likewise, we can easily isolate the 6th peak and return to the frequency-domain. This is impossible in the time-domain because there is too much broadening and overlap.

<img src="https://raw.githubusercontent.com/garrettj403/DispersionTransform/main/examples/results/cavity-peak6.jpg" width="500">

Note: This example is similar to the example presented by [Garrett & Tong 2021](https://ieeexplore.ieee.org/document/9447194), but it is slightly different (e.g., different dimensions, different iris parameters, etc.). Please see this paper for more information.

Citing This Repo
----------------

If you use this code, please cite the following paper:

    @article{Garrett2021,
      author       = {John D. Garrett and
                      Edward Tong},
      title        = {{A Dispersion-Compensated Algorithm for the Analysis of Electromagnetic Waveguides}},
      month        = jun,
      year         = 2021,
      journal      = {IEEE Signal Processing Letters},
      doi          = {10.1109/LSP.2021.3086695},
      url          = {https://ieeexplore.ieee.org/document/9447194}
    }
