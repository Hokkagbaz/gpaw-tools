---
layout: default
navigation_weight: 6
title: Input File Keywords
---

# Input File Keywords

```
NOTE: This page is under construction.
```
## General Keywords

---

### Mode
#### Keyword type
String

#### Description
This keyword controls the running mode of the GPAW. Available options are:

* PW
* PW-GW
* EXX
* LCAO
* FD.

#### Default
PW

#### Example
Mode = 'PW'

---

### DOS_calc
#### Keyword type
Logical

#### Description
This keyword controls the performing of DOS calculations or not. Available options are:

* True
* False

#### Default
False

#### Example
DOS_calc = True

---

### Band_calc
#### Keyword type
Logical

#### Description
This keyword controls the performing of Band calculations or not. Available options are:

* True
* False

#### Default
False

#### Example
Band_calc = False

---

### Density_calc
#### Keyword type
Logical

#### Description
This keyword controls the performing of electron density calculations or not. Available options are:

* True
* False

#### Default
False

#### Example
Density_calc = True

---

### Optical_calc
#### Keyword type
Logical

#### Description
This keyword controls the performing of optical calculations or not. Must be used independently from DOS_calc, Band_calc and Density_calc. Please visit examples directory for the example usage. Available options are:

* True
* False

#### Default
False

#### Example
Optical_calc = False

---
## Electronic Properties Calculation Variables
### fmaxval
#### Keyword type
Floating point

#### Description
This keyword controls the maximum force tolerance in BFGS type geometry optimization. Unit is eV/Ang.

#### Default
0.05

#### Example
fmaxval = 0.05 # eV/Ang

---

### cut_off_energy
#### Keyword type
Integer

#### Description
This keyword controls the plane wave cut off energy value. Unit is eV. Can be used in PW mode.

#### Default
340 eV

#### Example
cut_off_energy = 500 # eV

---

### kpts_density
#### Keyword type
Floating point

#### Description
This keyword controls kpoint density. It is deactivated normally. Monkhorst-Pack mesh is used with `kpts_x`, `kpts_y` and `kpts_z` variables. If `kpts_density` is included in an input file, the `kpts_x`, `kpts_y` and `kpts_z` variables will be ignored automatically. Unit is pts per Å^-1.

#### Default
Not used in default.

#### Example
kpts_density = 2.5     # pts per Å^-1

---

### kpts_x
#### Keyword type
Integer

#### Description
This keyword controls the number of kpoints in x direction. If `kpts_density` is included in an input file, the `kpts_x` variable will be ignored automatically. Unit is number of points.

#### Default
5

#### Example
kpts_x = 5

---

### kpts_y
#### Keyword type
Integer

#### Description
This keyword controls the number of kpoints in y direction. If `kpts_density` is included in an input file, the `kpts_y` variable will be ignored automatically. Unit is number of points.

#### Default
5

#### Example
kpts_y = 5

---

### kpts_z
#### Keyword type
Integer

#### Description
This keyword controls the number of kpoints in z direction. If `kpts_density` is included in an input file, the `kpts_z` variable will be ignored automatically. Unit is number of points.

#### Default
5

#### Example
kpts_z = 5
