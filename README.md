Dispersion-Compensated Algorithm
================================

*Dispersion-Compensated Algorithm for the Analysis for Electromagnetic Waveguides*

This package allows you to map dispersive waveguide data from the frequency-domain to distance-domain, and vice versa.

For more information, see: 

   - J. D. Garrett and C. E. Tong, ["A Dispersion-Compensated Algorithm for the Analysis of Electromagnetic Waveguides",](https://ieeexplore.ieee.org/document/9447194) *IEEE Signal Processing Letters*, Jun. 2021, doi: [10.1109/LSP.2021.3086695](https://doi.org/10.1109/LSP.2021.3086695).

Example: Waveguide Cavity Resonator
-----------------------------------

Frequency-domain:

<img src="https://github.com/garrettj403/DispersionTransform/raw/master/examples/results/cavity-freq-domain.jpg" width="500">

Distance-domain:

<img src="https://github.com/garrettj403/DispersionTransform/raw/master/examples/results/cavity-distance-domain.jpg" width="500">

Isolating peak #1:

<img src="https://github.com/garrettj403/DispersionTransform/raw/master/examples/results/cavity-peak1.jpg" width="500">

Isolating peak #6:

<img src="https://github.com/garrettj403/DispersionTransform/raw/master/examples/results/cavity-peak6.jpg" width="500">

Note: This example is similar to the example presented by [Garrett & Tong 2021](https://ieeexplore.ieee.org/document/9447194), but it is slightly different (e.g., different dimensions, different iris parameters, etc.).

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
