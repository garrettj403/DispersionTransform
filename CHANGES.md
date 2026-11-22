v0.1.0 (unreleased)
===================

- Add input validation: ``freq2distance`` and ``distance2freq`` now raise ``ValueError`` for mismatched lengths, non-uniform ``x``, ``x`` with fewer than 2 points (``distance2freq``), complex or non-monotonic ``beta``, and non-finite values. Previously, some of these cases silently returned incorrect results.
- ``freq2distance``: ``x`` is now optional (see ``default_distance``).
- Add ``default_distance`` and ``gate`` (distance-domain windowing) functions.
- ``distance2freq``: use ``np.gradient`` for the phase constant step, which also fixes the case where ``beta`` has only 2 points.
- Speed up the transforms (parallel Numba kernels, cached compilation).
- Add ``disptrans.__version__``.
- Packaging: replace ``setup.py`` with ``pyproject.toml`` (fixes installation with setuptools >= 72); require Python >= 3.10.
- CI: test Python 3.10-3.13 and update GitHub Actions.
- Tests: support scikit-rf >= 1.0.

v0.0.1 (21-Oct-2021)
====================

Initial release.
