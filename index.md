---
layout: default
navigation_weight: 1
title: Home
---

# Welcome to *gpaw-tools*

## Introduction
*gpaw-tools* is a bunch for python scripts for easy performing of GPAW calculations. It is mostly written for new DFT users who are running codes in their own PCs or on small group clusters.

`gpaw-tools` have:
1. A force-field quick optimization script `quickoptimization.py` for preliminary calculations using ASAP3/OpenKIM potentials. 
2. `ciftoase.py` script for transform CIF files to ASE's own Atoms object.
3. To choose better cut off energy, lattice parameter and k points, there are 3 scripts called `optimize_cutoff.py`, `optimize_latticeparam.py` and `optimize_kpoints.py`.
4. And, the main solver script `gpawsolver.py` which can be run in PW or LCAO mode. It can do strain minimization, can use several different XCs, can do spin-polarized calculations, can calculate, draw and save tidily DOS and band structures, can calculate and save all-electron densities and can calculate optical properties in a very simple and organized way.

More information about [gpaw-tools idea](about.md), [installation](installation.md), [usage](usage.md) and [release notes](releasenotes.md) can be found at related pages.

## Download

**Latest stable release: v21.10.1 [download (tar.gz)](https://github.com/lrgresearch/gpaw-tools/archive/refs/tags/v21.10.1.tar.gz), [download (zip)](https://github.com/lrgresearch/gpaw-tools/archive/refs/tags/v21.10.1.zip)**

Latest development release: [download (tar.gz)](https://github.com/lrgresearch/gpaw-tools/archive/refs/heads/main.tar.gz), [download (zip)](https://github.com/lrgresearch/gpaw-tools/archive/refs/heads/main.zip)

## News
* **[gpaw-tools](releasenotes.md#version-21101)** version 21.10.1 released (Oct 1, 2021).
* **[gpaw-tools](releasenotes.md#version-21100)** version 21.10.0 released (Oct 1, 2021).
* **[gpaw-tools](releasenotes.md#version-2190)** version 21.9.0 released (Sep 14, 2021).

## Licensing
This project is licensed under the terms of the [MIT license](https://opensource.org/licenses/MIT).
