# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`disptrans` (PyPI) is the reference implementation of Garrett & Tong, "A Dispersion-Compensated Algorithm for the Analysis of Electromagnetic Waveguides" (IEEE SPL, 2021). It maps waveguide S-parameters between the frequency-domain and the distance-domain using the phase constant β(f), so reflections stay sharp instead of broadening with dispersion like they do after a plain IFFT.

## Commands

```bash
pip install -e ".[testing]"     # dev install (quote the extras for zsh)
pip install -e ".[examples]"    # notebook deps (matplotlib, scikit-rf, SciencePlots)

pytest                          # all tests (testpaths is set in pyproject.toml)
pytest -k test_gate             # single test / pattern
pytest "test_disptrans.py::test_roundtrip[lossy]"   # single parametrized case
python test_disptrans.py        # plot original vs. recovered round trip (manual check)

flake8 .                        # lint (max line length 120, see .flake8)
python -m build                 # sdist + wheel
```

Re-run the example notebooks from inside `examples/`. They write the README figures to `examples/results/`:

```bash
cd examples && jupyter nbconvert --to notebook --execute --inplace waveguide-cavity.ipynb
```

## Architecture

The whole library is the single module `disptrans.py` (`py-modules`, not a package). It has two layers:

- **Public functions** (`freq2distance`, `distance2freq`, `default_distance`, `gate`) validate and cast all inputs in Python. They raise `ValueError` for mismatched lengths, non-uniform or single-point `x`, complex or non-monotonic `beta` (points below cutoff), and non-finite values. They then call the kernels with contiguous `float64`/`complex128` arrays.
- **Numba kernels** (`_freq2distance`, `_distance2freq`) use `@nb.njit(parallel=True, cache=True)` and are O(N·M) sums over `exp(±jβx)`. Numba does no bounds checking, so a kernel must never see unvalidated input: before validation was added, bad input silently returned garbage. Keep each kernel's inputs to a single dtype signature to avoid recompiles.

The maths that is easy to get wrong:
- `freq2distance` multiplies by `e^{+jβx}`, which matches scikit-rf's `S21 = e^{-jβd}`, and normalizes by `1/N`.
- `distance2freq` multiplies by `e^{-jβx}` and normalizes by `N · Δx · Δβ / (2π)`. `Δβ = np.gradient(beta)` is the Jacobian that turns the sum over frequency points into an integral over β, which is why non-uniform β is fine but `x` must be uniform. The output grid is set by `beta`, so `f` is only checked for length.
- `default_distance` is the IFFT-time-axis analogue: it covers one unambiguous range `2π / mean(Δβ)` starting at 0.

## Tests

`test_disptrans.py` builds WR-2.8 waveguides with scikit-rf. Always pass `rho` explicitly: `rho=None` means lossless. scikit-rf ≥ 1.0 defaults to copper walls, so leaving `rho` out quietly makes the "lossless" case lossy. Round-trip checks compare only 265–395 GHz to avoid edge effects. `test_matches_reference_implementation` checks both kernels against a plain-NumPy version, so update it whenever you change a normalization.

## Versioning and releases

- The version lives only in `disptrans.__version__`; `pyproject.toml` reads it dynamically.
- To release: bump `__version__`, add a dated entry to `CHANGES.md`, then push a `vX.Y.Z` tag. `.github/workflows/publish.yml` checks that the tag matches `__version__`, builds, tests the built wheel, and publishes to PyPI through trusted publishing (no token).
- CI (`ci.yml`) runs pytest on Ubuntu, Windows and macOS × Python 3.10–3.13, and `linter.yml` runs flake8. The notebooks are not run in CI.

## Other notes

- `references/` (the paper manuscript) is gitignored on purpose; don't commit it.
- README figures are linked by absolute `raw.githubusercontent.com/.../main/...` URLs, so renaming a file in `examples/results/` breaks the README.
