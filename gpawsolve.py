#!/usr/bin/env python

'''
gpawsolve.py: High-level Interaction Script for GPAW
More information: $ gpawsolve.py -h
'''

Description = f'''
 Usage: 
 $ mpirun -np <corenumbers> gpawsolve.py <args>
 -------------------------------------------------------------
 Calculation selector
 -------------------------------------------------------------
 | Method | XCs             | Structure optim. | Spin | Ground | Elastic | DOS | DFT+U | Band | Density | Optical |
 | ------ | --------------- | ---------------- | ---- | ------ | ------- | --- | ----- | ---- | ------- | ------- |
 |   PW   | Local and LibXC | Yes              | Yes  | Yes    | Yes     | Yes | Yes   | Yes  | Yes     | Yes     |
 |   PW   | GLLBSC / M      | No               | Yes  | Yes    | Yes     | Yes | No    | Yes  | Yes     | Yes     |
 |   PW   | HSE03, HSE06    | No               | Yes  | Yes    | n/a     | Yes | No    | No   | No      | No      |
 | PW-G0W0| Local and LibXC | No               | No   | Yes    | No      | No  | No    | Some | No      | No      |
 | PW-EXX*| B3LYP, PBE0     | Yes (with PBE)   | No   | Yes    | No      | No  | No    | No   | No      | No      |
 |  LCAO  | Local and LibXC | Yes              | Yes  | Yes    | Yes     | Yes | Yes   | Yes  | Yes     | No      |
 *: Just some ground state energy calculations.
'''

import getopt, sys, os, time, shutil
import textwrap
import requests
import pickle
import spglib as spg
from argparse import ArgumentParser, HelpFormatter
from ase import *
from ase.dft.kpoints import get_special_points
from ase.parallel import paropen, world, parprint, broadcast
from gpaw import GPAW, PW, Davidson, FermiDirac, MixerSum, MixerDif, Mixer
from ase.optimize import QuasiNewton
from ase.io import read, write
from ase.eos import calculate_eos
from ase.units import Bohr, GPa, kJ
import matplotlib.pyplot as plt
from ase.constraints import ExpCellFilter
from ase.spacegroup.symmetrize import FixSymmetry
from ase.io.cif import write_cif
from pathlib import Path
from gpaw.response.df import DielectricFunction
from gpaw.response.bse import BSE
from gpaw.response.g0w0 import G0W0
from gpaw.response.gw_bands import GWBands
from gpaw.xc.exx import EXX
from gpaw.dos import DOSCalculator
import numpy as np
from numpy import genfromtxt
from elastic import get_elastic_tensor, get_elementary_deformations
from phonopy import Phonopy
from phonopy.structure.atoms import PhonopyAtoms
from phonopy.phonon.band_structure import get_band_qpoints_and_path_connections
import phonopy

class RawFormatter(HelpFormatter):
    """To print Description variable with argparse"""
    def _fill_text(self, text, width, indent):
        return "\n".join([textwrap.fill(line, width) for line in textwrap.indent(textwrap.dedent(text), indent).splitlines()])

def struct_from_file(inputfile, geometryfile):
    """Load variables from parse function"""
    global bulk_configuration
    # Works like from FILE import *
    inputf = __import__(Path(inputfile).stem, globals(), locals(), ['*'])
    for k in dir(inputf):
        # Still can not get rid of global variable usage :(
        globals()[k] = getattr(inputf, k)            
    # If there is a CIF input, use it. Otherwise use the bulk configuration provided above.
    if geometryfile is None:
        if Outdirname !='':
            struct = Outdirname
        else:
            struct = 'results' # All files will get their names from this file
    else:
        struct = Path(geometryfile).stem
        bulk_configuration = read(geometryfile, index='-1')
        parprint("Number of atoms imported from CIF file:"+str(bulk_configuration.get_global_number_of_atoms()))
        parprint("Spacegroup of CIF file (from SPGlib):",spg.get_spacegroup(bulk_configuration))
        parprint("Special Points usable for this spacegroup:",get_special_points(bulk_configuration.get_cell()))

    # Output directory
    if Outdirname != '':
        structpath = os.path.join(os.getcwd(),Outdirname)
    else:
        structpath = os.path.join(os.getcwd(),struct)

    if not os.path.isdir(structpath):
        os.makedirs(structpath, exist_ok=True)
    struct = os.path.join(structpath,struct)
    return struct
    
class gpawsolve:
    """
    The gpawsolve class is a high-level interaction script for GPAW calculations.
    It handles various types of calculations such as ground state, structure optimization,
    elastic properties, density of states, band structure, density, and optical properties.
    The class takes input parameters from a configuration file and performs the calculations
    accordingly.
    """
    def __init__(self, struct):
        global np   
        self.Mode = Mode
        self.Geo_optim = Geo_optim
        self.Elastic_calc = Elastic_calc
        self.DOS_calc = DOS_calc
        self.Band_calc = Band_calc
        self.Density_calc = Density_calc
        self.Optical_calc = Optical_calc
        self.Optimizer = Optimizer
        self.Max_F_tolerance = Max_F_tolerance
        self.Max_step = Max_step
        self.Alpha = Alpha
        self.Damping = Damping
        self.Fix_symmetry = Fix_symmetry
        self.Relax_cell = Relax_cell
        self.Cut_off_energy = Cut_off_energy
        self.Ground_kpts_x = Ground_kpts_x
        self.Ground_kpts_y = Ground_kpts_y
        self.Ground_kpts_z = Ground_kpts_z
        self.Ground_gpts_dens = Ground_gpts_dens
        self.Ground_gpts_x = Ground_gpts_x
        self.Ground_gpts_y = Ground_gpts_y
        self.Ground_gpts_z = Ground_gpts_z
        self.Setup_params = Setup_params
        self.XC_calc = XC_calc
        self.Ground_convergence = Ground_convergence
        self.Occupation = Occupation
        self.Mixer_type = Mixer_type
        self.Spin_calc = Spin_calc
        self.Magmom_per_atom = Magmom_per_atom
        self.DOS_npoints = DOS_npoints
        self.DOS_width = DOS_width
        self.DOS_convergence = DOS_convergence
        self.Gamma = Gamma
        self.Band_path = Band_path
        self.Band_npoints = Band_npoints
        self.Energy_max = Energy_max
        self.Energy_min = Energy_min
        self.Band_convergence = Band_convergence
        self.Refine_grid = Refine_grid
        self.Phonon_PW_cutoff = Phonon_PW_cutoff
        self.Phonon_kpts_x = Phonon_kpts_x
        self.Phonon_kpts_y = Phonon_kpts_y
        self.Phonon_kpts_z = Phonon_kpts_z
        self.Phonon_supercell = Phonon_supercell
        self.Phonon_displacement = Phonon_displacement
        self.Phonon_path = Phonon_path
        self.Phonon_npoints = Phonon_npoints
        self.Phonon_acoustic_sum_rule = Phonon_acoustic_sum_rule
        self.GW_calc_type = GW_calc_type
        self.GW_kpoints_list = GW_kpoints_list
        self.GW_truncation = GW_truncation
        self.GW_cut_off_energy = GW_cut_off_energy
        self.GW_valence_band_no = GW_valence_band_no
        self.GW_conudction_band_no = GW_conudction_band_no
        self.GW_PPA = GW_PPA
        self.GW_q0_correction = GW_q0_correction
        self.GW_nblocks_max = GW_nblocks_max
        self.GW_interpolate_band = GW_interpolate_band
        self.Opt_calc_type = Opt_calc_type
        self.Opt_shift_en = Opt_shift_en
        self.Opt_BSE_valence = Opt_BSE_valence
        self.Opt_BSE_conduction = Opt_BSE_conduction
        self.Opt_BSE_min_en = Opt_BSE_min_en
        self.Opt_BSE_max_en = Opt_BSE_max_en
        self.Opt_BSE_num_of_data = Opt_BSE_num_of_data
        self.Opt_num_of_bands = Opt_num_of_bands
        self.Opt_FD_smearing = Opt_FD_smearing
        self.Opt_eta = Opt_eta
        self.Opt_domega0 = Opt_domega0
        self.Opt_omega2 = Opt_omega2
        self.Opt_cut_of_energy = Opt_cut_of_energy
        self.Opt_nblocks = Opt_nblocks
        self.MPI_cores = MPI_cores
        self.bulk_configuration = bulk_configuration
        self.struct = struct

    def structurecalc(self):
        """
        This method calculates and writes the spacegroup and special points of the given structure.
        It reads the bulk configuration from the CIF file and prints the number of atoms, spacegroup,
        and special points usable for the spacegroup to a text file.
        """

        # -------------------------------------------------------------
        # Step 0 - STRUCTURE
        # -------------------------------------------------------------
        
        with paropen(struct+'-0-Result-Spacegroup-and-SpecialPoints.txt', "w") as fd:
            print("Number of atoms imported from CIF file:"+str(bulk_configuration.get_global_number_of_atoms()), file=fd)
            print("Spacegroup of CIF file (from SPGlib):",spg.get_spacegroup(bulk_configuration), file=fd)
            print("Special Points usable for this spacegroup:",get_special_points(bulk_configuration.get_cell()), file=fd)

    def groundcalc(self):
        """
        This method performs ground state calculations for the given structure using various settings
        and parameters specified in the configuration file. It handles different XC functionals,
        spin calculations, and geometry optimizations. The results are saved in appropriate files,
        including the final configuration as a CIF file and the ground state results in a GPW file.
        """
        
        # -------------------------------------------------------------
        # Step 1 - GROUND STATE
        # -------------------------------------------------------------
        
        # Start ground state timing
        time11 = time.time()
        if Mode == 'PW':
            if XC_calc in ['B3LYP', 'PBE0']:
                parprint('\033[91mERROR:\033[0m'+XC_calc+' can be used only in PW-EXX mode...')
                quit()
            if Spin_calc == True:
                numm = [Magmom_per_atom]*bulk_configuration.get_global_number_of_atoms()
                bulk_configuration.set_initial_magnetic_moments(numm)
            if passground == False:
                # PW Ground State Calculations
                parprint("Starting PW ground state calculation...")
                if True in Relax_cell:
                    if XC_calc in ['GLLBSC', 'GLLBSCM', 'HSE06', 'HSE03']:
                        parprint("\033[91mERROR:\033[0m Structure optimization LBFGS can not be used with "+XC_calc+" xc.")
                        parprint("Do manual structure optimization, or do with PBE, then use its final CIF as input.")
                        parprint("Quiting...")
                        quit()
                if XC_calc in ['HSE06', 'HSE03']:
                    parprint('Starting Hybrid XC calculations...')
                    if 'Ground_kpts_density' in globals():
                        calc = GPAW(mode=PW(Cut_off_energy), xc={'name': XC_calc, 'backend': 'pw'}, nbands='200%', parallel={'band': 1, 'kpt': 1},
                                eigensolver=Davidson(niter=1), mixer=Mixer_type,
                                spinpol=Spin_calc, kpts={'density': Ground_kpts_density, 'gamma': Gamma}, txt=struct+'-1-Log-Ground.txt',
                                convergence = Ground_convergence, occupations = Occupation)
                    else:
                        calc = GPAW(mode=PW(Cut_off_energy), xc={'name': XC_calc, 'backend': 'pw'}, nbands='200%', parallel={'band': 1, 'kpt': 1},
                                eigensolver=Davidson(niter=1), mixer=Mixer_type,
                                spinpol=Spin_calc, kpts={'size': (Ground_kpts_x, Ground_kpts_y, Ground_kpts_z), 'gamma': Gamma}, txt=struct+'-1-Log-Ground.txt',
                                convergence = Ground_convergence, occupations = Occupation)
                else:
                    parprint('Starting calculations with '+XC_calc+'...')
                    # Fix the spacegroup in the geometric optimization if wanted
                    if Fix_symmetry == True:
                        bulk_configuration.set_constraint(FixSymmetry(bulk_configuration))
                    if 'Ground_kpts_density' in globals():
                        calc = GPAW(mode=PW(Cut_off_energy), xc=XC_calc, nbands='200%', setups= Setup_params, parallel={'domain': world.size},
                                spinpol=Spin_calc, kpts={'density': Ground_kpts_density, 'gamma': Gamma},
                                mixer=Mixer_type, txt=struct+'-1-Log-Ground.txt',
                                convergence = Ground_convergence, occupations = Occupation)
                    else:
                        calc = GPAW(mode=PW(Cut_off_energy), xc=XC_calc, nbands='200%', setups= Setup_params, parallel={'domain': world.size},
                                spinpol=Spin_calc, kpts={'size': (Ground_kpts_x, Ground_kpts_y, Ground_kpts_z), 'gamma': Gamma},
                                mixer=Mixer_type, txt=struct+'-1-Log-Ground.txt',
                                convergence = Ground_convergence, occupations = Occupation)
                bulk_configuration.calc = calc
                if Geo_optim == True:
                    if True in Relax_cell:
                        uf = ExpCellFilter(bulk_configuration, mask=Relax_cell)
                        # Optimizer Selection
                        if Optimizer == 'FIRE':
                            from ase.optimize.fire import FIRE
                            relax = FIRE(uf, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                        elif  Optimizer == 'LBFGS':
                            from ase.optimize.lbfgs import LBFGS
                            relax = LBFGS(uf, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                        elif  Optimizer == 'GPMin':
                            from ase.optimize import GPMin
                            relax = GPMin(uf, trajectory=struct+'-1-Result-Ground.traj')
                        else:
                            relax = QuasiNewton(uf, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                    else:
                        # Optimizer Selection
                        if Optimizer == 'FIRE':
                            from ase.optimize.fire import FIRE
                            relax = FIRE(bulk_configuration, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                        elif  Optimizer == 'LBFGS':
                            from ase.optimize.lbfgs import LBFGS
                            relax = LBFGS(bulk_configuration, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                        elif  Optimizer == 'GPMin':
                            from ase.optimize import GPMin
                            relax = GPMin(bulk_configuration, trajectory=struct+'-1-Result-Ground.traj')
                        else:
                            relax = QuasiNewton(bulk_configuration, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                    relax.run(fmax=Max_F_tolerance)  # Consider tighter fmax!
                else:
                    bulk_configuration.set_calculator(calc)
                    bulk_configuration.get_potential_energy()
                if Density_calc == True:
                    #This line makes huge GPW files. Therefore it is better to use this if else
                    calc.write(struct+'-1-Result-Ground.gpw', mode="all")
                else:
                    calc.write(struct+'-1-Result-Ground.gpw')
                # Writes final configuration as CIF file
                write_cif(struct+'-Final.cif', bulk_configuration)
            else:
                parprint("Passing PW ground state calculation...")
                # Control the ground state GPW file
                if not os.path.exists(struct+'-1-Result-Ground.gpw'):
                    parprint('\033[91mERROR:\033[0m'+struct+'-1-Result-Ground.gpw file can not be found. It is needed in passing mode. Quiting.')
                    quit()

        elif Mode == 'PW-EXX':
            if passground == False:
                # PW Ground State Calculations
                parprint("Starting PW ground state calculation with PBE...")
                # Fix the spacegroup in the geometric optimization if wanted
                if Fix_symmetry == True:
                    bulk_configuration.set_constraint(FixSymmetry(bulk_configuration))
                if 'Ground_kpts_density' in globals():
                    calc = GPAW(mode=PW(Cut_off_energy), xc='PBE', parallel={'domain': world.size}, kpts={'density': Ground_kpts_density, 'gamma': Gamma},
                            convergence = Ground_convergence, mixer=Mixer_type, occupations = Occupation, txt=struct+'-1-Log-Ground.txt')
                else:
                    calc = GPAW(mode=PW(Cut_off_energy), xc='PBE', parallel={'domain': world.size}, 
                                kpts={'size': (Ground_kpts_x, Ground_kpts_y, Ground_kpts_z), 'gamma': Gamma},
                                convergence = Ground_convergence, mixer=Mixer_type, occupations = Occupation, txt=struct+'-1-Log-Ground.txt')
                bulk_configuration.calc = calc
                uf = ExpCellFilter(bulk_configuration, mask=Relax_cell)
                # Optimizer Selection
                if Optimizer == 'FIRE':
                    from ase.optimize.fire import FIRE
                    relax = FIRE(uf, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                elif  Optimizer == 'LBFGS':
                    from ase.optimize.lbfgs import LBFGS
                    relax = LBFGS(uf, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                elif  Optimizer == 'GPMin':
                    from ase.optimize import GPMin
                    relax = GPMin(uf, trajectory=struct+'-1-Result-Ground.traj')
                else:
                    relax = QuasiNewton(uf, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                relax.run(fmax=Max_F_tolerance)  # Consider tighter fmax!
                calc.write(struct+'-1-Result-Ground.gpw', mode="all")
                # Writes final configuration as CIF file
                write_cif(struct+'-Final.cif', bulk_configuration)
                # Print final spacegroup information
                parprint("Final Spacegroup (SPGlib):",spg.get_spacegroup(bulk_configuration))
            else:
                parprint("Passing PW ground state calculation...")
                # Control the ground state GPW file
                if not os.path.exists(struct+'-1-Result-Ground.gpw'):
                    parprint('\033[91mERROR:\033[0m'+struct+'-1-Result-Ground.gpw file can not be found. It is needed in passing mode. Quiting.')
                    quit()

            if XC_calc in ['B3LYP', 'PBE0']:
                parprint('Starting PW EXX ground state calculation with '+XC_calc+' ...')
                calc_exx = EXX(struct+'-1-Result-Ground.gpw', xc=XC_calc, txt=struct+'-1-Log-EXX_mode.txt')
                bulk_configuration.calc_exx = calc_exx
                with paropen(struct+'-1-Result-Ground-EXX_mode.txt', "w") as fd:
                    print('Eigenvalue contributions: ',calc_exx.get_eigenvalue_contributions() , file=fd)
                    if np.isnan(calc_exx.get_exx_energy()):
                        print ('The EXX and therefore total energy is not be calculated, because we are only', file=fd)
                        print ('interested in a few eigenvalues for a few k-points.', file=fd)
                    else:
                        print('EXX Energy: ',calc_exx.get_exx_energy() , file=fd)
                        print('Total Energy: ',calc_exx.get_total_energy() , file=fd)
                parprint('\033[94mINFORMATION:\033[0mEXX mode results are only listed at: '+struct+'-1-Result-Ground-EXX_mode.txt')
                parprint('          Other files (DOS, band, etc...) are the results calculated with PBE.')

        elif Mode == 'PW-GW':
            if passground == False:
                # PW Ground State Calculations
                parprint("Starting PW only ground state calculation for GW calculation...")
                # Fix the spacegroup in the geometric optimization if wanted
                if Fix_symmetry == True:
                    bulk_configuration.set_constraint(FixSymmetry(bulk_configuration))
                if 'Ground_kpts_density' in globals():
                    calc = GPAW(mode=PW(Cut_off_energy), xc=XC_calc, parallel={'domain': 1}, kpts={'density': Ground_kpts_density, 'gamma': Gamma},
                            convergence = Ground_convergence,
                            mixer=Mixer_type, occupations = Occupation, txt=struct+'-1-Log-Ground.txt')
                else:
                    calc = GPAW(mode=PW(Cut_off_energy), xc=XC_calc, parallel={'domain': 1}, kpts={'size':(Ground_kpts_x, Ground_kpts_y, Ground_kpts_z), 'gamma': Gamma},
                            convergence = Ground_convergence,
                            mixer=Mixer_type, occupations = Occupation, txt=struct+'-1-Log-Ground.txt')
                bulk_configuration.calc = calc
                uf = ExpCellFilter(bulk_configuration, mask=Relax_cell)
                # Optimizer Selection
                if Optimizer == 'FIRE':
                    from ase.optimize.fire import FIRE
                    relax = FIRE(uf, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                elif  Optimizer == 'LBFGS':
                    from ase.optimize.lbfgs import LBFGS
                    relax = LBFGS(uf, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                elif  Optimizer == 'GPMin':
                    from ase.optimize import GPMin
                    relax = GPMin(uf, trajectory=struct+'-1-Result-Ground.traj')
                else:
                    relax = QuasiNewton(uf, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                relax.run(fmax=Max_F_tolerance)  # Consider tighter fmax!
                bulk_configuration.get_potential_energy()
                calc.diagonalize_full_hamiltonian()
                calc.write(struct+'-1-Result-Ground.gpw', mode="all")
                # Writes final configuration as CIF file
                write_cif(struct+'-Final.cif', bulk_configuration)
                # Print final spacegroup information
                parprint("Final Spacegroup (SPGlib):",spg.get_spacegroup(bulk_configuration))
            else:
                parprint("Passing ground state calculation for GW calculation...")
                # Control the ground state GPW file
                if not os.path.exists(struct+'-1-Result-Ground.gpw'):
                    parprint('\033[91mERROR:\033[0m'+struct+'-1-Result-Ground.gpw file can not be found. It is needed in passing mode. Quiting.')
                    quit()

            # We start by setting up a G0W0 calculator object
            gw = G0W0(struct+'-1-Result-Ground.gpw', filename=struct+'-1-', bands=(GW_valence_band_no, GW_conduction_band_no),
                      method=GW_calc_type,truncation=GW_truncation, nblocksmax=GW_nblocks_max,
                      maxiter=5, q0_correction=GW_q0_correction,
                      mixing=0.5,savepckl=True,
                      ecut=GW_cut_off_energy, ppa=GW_PPA)
            parprint("Starting PW ground state calculation with G0W0 approximation...")
            gw.calculate()
            results = pickle.load(open(struct+'-1-_results.pckl', 'rb'))
            with paropen(struct+'-1-BandGap.txt', "w") as fd:
                print('Quasi particle (QP) energies in eV. Take CB-VB for the bandgap', file=fd)
                print('To see other energy contributions, use python -mpickle <picklefile>', file=fd)
                for x in zip(results['qp']):
                    print(*x, sep=", ", file=fd)

        elif Mode == 'LCAO':
            if Spin_calc == True:
                numm = [Magmom_per_atom]*bulk_configuration.get_global_number_of_atoms()
                bulk_configuration.set_initial_magnetic_moments(numm)
            if passground == False:
                parprint("Starting LCAO ground state calculation...")
                # Fix the spacegroup in the geometric optimization if wanted
                if Fix_symmetry == True:
                    bulk_configuration.set_constraint(FixSymmetry(bulk_configuration))
                if 'Ground_gpts_dens' in globals():
                    if 'Ground_kpts_density' in globals():
                        calc = GPAW(mode='lcao', basis='dzp', setups= Setup_params, kpts={'density': Ground_kpts_density, 'gamma': Gamma},
                                convergence = Ground_convergence, h=Ground_gpts_dens, spinpol=Spin_calc, txt=struct+'-1-Log-Ground.txt',
                                mixer=Mixer_type, occupations = Occupation, parallel={'domain': world.size})
                    else:
                        calc = GPAW(mode='lcao', basis='dzp', setups= Setup_params, kpts={'size':(Ground_kpts_x, Ground_kpts_y, Ground_kpts_z), 'gamma': Gamma},
                                convergence = Ground_convergence, h=Ground_gpts_dens, spinpol=Spin_calc, txt=struct+'-1-Log-Ground.txt',
                                mixer=Mixer_type, occupations = Occupation, parallel={'domain': world.size})
                else:
                    if 'Ground_kpts_density' in globals():
                        calc = GPAW(mode='lcao', basis='dzp', setups= Setup_params, kpts={'density': Ground_kpts_density, 'gamma': Gamma},
                                convergence = Ground_convergence, gpts=(Ground_gpts_x, Ground_gpts_y, Ground_gpts_z), spinpol=Spin_calc, txt=struct+'-1-Log-Ground.txt',
                                mixer=Mixer_type, occupations = Occupation, parallel={'domain': world.size})
                    else:
                        calc = GPAW(mode='lcao', basis='dzp', setups= Setup_params, kpts={'size':(Ground_kpts_x, Ground_kpts_y, Ground_kpts_z), 'gamma': Gamma},
                                convergence = Ground_convergence, gpts=(Ground_gpts_x, Ground_gpts_y, Ground_gpts_z), spinpol=Spin_calc, txt=struct+'-1-Log-Ground.txt',
                                mixer=Mixer_type, occupations = Occupation, parallel={'domain': world.size})
                bulk_configuration.calc = calc
                if Geo_optim == True:
                    if True in Relax_cell:
                        #uf = ExpCellFilter(bulk_configuration, mask=Relax_cell)
                        #relax = LBFGS(uf, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                        parprint('\033[91mERROR:\033[0mModifying supercell and atom positions with a filter (Relax_cell keyword) is not implemented in LCAO mode.')
                        quit()
                    else:
                        # Optimizer Selection
                        if Optimizer == 'FIRE':
                            from ase.optimize.fire import FIRE
                            relax = FIRE(bulk_configuration, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                        elif Optimizer == 'LBFGS':
                            from ase.optimize.lbfgs import LBFGS
                            relax = LBFGS(bulk_configuration, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                        elif Optimizer == 'GPMin':
                            from ase.optimize import GPMin
                            relax = GPMin(bulk_configuration, trajectory=struct+'-1-Result-Ground.traj')
                        else:
                            relax = QuasiNewton(bulk_configuration, maxstep=Max_step, trajectory=struct+'-1-Result-Ground.traj')
                    relax.run(fmax=Max_F_tolerance)  # Consider tighter fmax!
                else:
                    bulk_configuration.set_calculator(calc)
                    bulk_configuration.get_potential_energy()
                #relax = LBFGS(bulk_configuration, maxstep=Max_step, alpha=Alpha, damping=Damping, trajectory=struct+'-1-Result-Ground.traj')
                #relax.run(fmax=Max_F_tolerance)  # Consider much tighter fmax!
                #bulk_configuration.get_potential_energy()
                if Density_calc == True:
                    #This line makes huge GPW files. Therefore it is better to use this if else
                    calc.write(struct+'-1-Result-Ground.gpw', mode="all")
                else:
                    calc.write(struct+'-1-Result-Ground.gpw')
                # Writes final configuration as CIF file
                write_cif(struct+'-Final.cif', bulk_configuration)
                # Print final spacegroup information
                parprint("Final Spacegroup (SPGlib):",spg.get_spacegroup(bulk_configuration))
            else:
                parprint("Passing LCAO ground state calculation...")
                # Control the ground state GPW file
                if not os.path.exists(struct+'-1-Result-Ground.gpw'):
                    parprint('\033[91mERROR:\033[0m'+struct+'-1-Result-Ground.gpw file can not be found. It is needed in passing mode. Quiting.')
                    quit()

        elif Mode == 'FD':
            parprint("\033[91mERROR:\033[0mFD mode is not implemented in gpaw-tools yet...")
            quit()
        else:
            parprint("\033[91mERROR:\033[0mPlease enter correct mode information.")
            quit()
        # Finish ground state timing
        time12 = time.time()
        
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('Ground state: ', round((time12-time11),2), end="\n", file=f1)

    def elasticcalc(self, drawfigs = False):
        """
        This method performs elastic property calculations for the given structure using the
        ground state results. It computes the elastic constants, bulk modulus, shear modulus,
        and other related properties. The results are saved in appropriate files for further
        analysis and visualization.
        """

        # -------------------------------------------------------------
        # Step 1.5 - ELASTIC CALCULATION
        # -------------------------------------------------------------
        
        # Start elastic calc
        time151 = time.time()
        parprint('Starting elastic tensor calculations (\033[93mWARNING:\033[0mNOT TESTED FEATURE, PLEASE CONTROL THE RESULTS)...')
        calc = GPAW(struct+'-1-Result-Ground.gpw', fixdensity=True, txt=struct+'-1.5-Log-Elastic.txt')
        # Getting space group from SPGlib
        parprint('Spacegroup:',spg.get_spacegroup(bulk_configuration))
        # Calculating equation of state
        parprint('Calculating equation of state...')
        eos = calculate_eos(bulk_configuration, trajectory=struct+'-1-Result-Ground.traj')
        v, e, B = eos.fit()
        # Calculating elastic tensor
        parprint('Calculating elastic tensor...')
        Cij, Bij=get_elastic_tensor(bulk_configuration,get_elementary_deformations(bulk_configuration, n=5, d=2))
        with paropen(struct+'-1.5-Result-Elastic.txt', "w") as fd:
            print("Elastic calculation results (NOT TESTED FEATURE, PLEASE CONTROL THE RESULTS):", file=fd)
            print("EoS: Stabilized jellium equation of state (SJEOS)", file=fd)
            print("Refs: Phys.Rev.B 63, 224115 (2001) and Phys.Rev.B 67, 026103 (2003)", file=fd)
            print("Elastic constants: Standart elasticity theory calculated by -Elastic- library", file=fd)
            print("Ref: European Physical Journal B; 15, 2 (2000) 265-268", file=fd)
            print("-----------------------------------------------------------------------------", file=fd)
            print("Spacegroup: "+str(spg.get_spacegroup(bulk_configuration)), file=fd)
            print("B (GPa): "+str(B / kJ * 1.0e24), file=fd)
            print("e (eV): "+str(e), file=fd)
            print("v (Ang^3): "+str(v), file=fd)
            print("Cij (GPa): ",Cij/GPa, file=fd)
            print("The general ordering of Cij components is (except triclinic): C11,C22,C33,C12,C13,C23,C44,C55,C66,C16,C26,C36,C45.", file=fd)
        # Finish elastic calc
        time152 = time.time()
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('Elastic calculation: ', round((time152-time151),2), end="\n", file=f1)

        # Draw or write the figure
        if drawfigs == True:
            # Draw graphs only on master node
            if world.rank == 0:
                # Elastic
                eos.plot(struct+'-1.5-Graph-Elastic-EOS.png', show=True)
        else:
            # Draw graphs only on master node
            if world.rank == 0:
                # Elastic
                eos.plot(struct+'-1.5-Result-Elastic-EOS.png')

        
    def doscalc(self, drawfigs = False):     
        """
        This method performs density of states (DOS) calculations for the given structure using
        the ground state results. It computes the DOS for various energy levels and saves the
        results in appropriate files for further electronic analysis and visualization.
        """

        # -------------------------------------------------------------
        # Step 2 - DOS CALCULATION
        # -------------------------------------------------------------
        
        # Start DOS calc
        time21 = time.time()
        parprint("Starting DOS calculation...")
        
        calc = GPAW(struct+'-1-Result-Ground.gpw', fixdensity=True, txt=struct+'-2-Log-DOS.txt', convergence = DOS_convergence, occupations = Occupation)
        
        chem_sym = bulk_configuration.get_chemical_symbols()
        #ef = calc.get_fermi_level()

        if Spin_calc == True:
            #Spin down

            # RAW PDOS for spin down
            parprint("Calculating and saving Raw PDOS for spin down...")
            rawdos = DOSCalculator.from_calculator(struct+'-1-Result-Ground.gpw',soc=False, theta=0.0, phi=0.0, shift_fermi_level=True)
            energies = rawdos.get_energies(npoints=DOS_npoints)
            totaldosweightsdown = [0.0] * DOS_npoints
            
            # Writing RawPDOS
            with paropen(struct+'-2-Result-RawPDOS-Down.csv', "w") as fd:
                print("Energy, s-total, p-total, px, py, pz, d-total, dxy, dyz, d3z2_r2, dzx, dx2_y2, f-total, TOTAL", file=fd)
                for j in range(0, bulk_configuration.get_global_number_of_atoms()):
                    print("Atom no: "+str(j+1)+", Atom Symbol: "+chem_sym[j]+" --------------------", file=fd)
                    pdoss = rawdos.raw_pdos(energies, a=j, l=0, m=None, spin=0, width=DOS_width)
                    pdosp = rawdos.raw_pdos(energies, a=j, l=1, m=None, spin=0, width=DOS_width)
                    pdospx = rawdos.raw_pdos(energies, a=j, l=1, m=2, spin=0, width=DOS_width)
                    pdospy = rawdos.raw_pdos(energies, a=j, l=1, m=0, spin=0, width=DOS_width)
                    pdospz = rawdos.raw_pdos(energies, a=j, l=1, m=1, spin=0, width=DOS_width)
                    pdosd = rawdos.raw_pdos(energies, a=j, l=2, m=None, spin=0, width=DOS_width)
                    pdosdxy = rawdos.raw_pdos(energies, a=j, l=2, m=0, spin=0, width=DOS_width)
                    pdosdyz = rawdos.raw_pdos(energies, a=j, l=2, m=1, spin=0, width=DOS_width)
                    pdosd3z2_r2 = rawdos.raw_pdos(energies, a=j, l=2, m=2, spin=0, width=DOS_width)
                    pdosdzx = rawdos.raw_pdos(energies, a=j, l=2, m=3, spin=0, width=DOS_width)
                    pdosdx2_y2 = rawdos.raw_pdos(energies, a=j, l=2, m=4, spin=0, width=DOS_width)
                    pdosf = rawdos.raw_pdos(energies, a=j, l=3, m=None, spin=0, width=DOS_width)
                    dosspdf = pdoss + pdosp + pdosd + pdosf
                    totaldosweightsdown = totaldosweightsdown + dosspdf
                    for x in zip(energies, pdoss, pdosp, pdospx, pdospy, pdospz, pdosd, pdosdxy, pdosdyz, pdosd3z2_r2, pdosdzx, pdosdx2_y2, pdosf, dosspdf):
                        print(*x, sep=", ", file=fd)
            
            # Writing DOS
            with paropen(struct+'-2-Result-DOS-Down.csv', "w") as fd:
                for x in zip(energies, totaldosweightsdown):
                    print(*x, sep=", ", file=fd)
            #Spin up

            # RAW PDOS for spin up
            parprint("Calculating and saving Raw PDOS for spin up...")
            rawdos = DOSCalculator.from_calculator(struct+'-1-Result-Ground.gpw',soc=False, theta=0.0, phi=0.0, shift_fermi_level=True)
            energies = rawdos.get_energies(npoints=DOS_npoints)
            totaldosweightsup = [0.0] * DOS_npoints
            
            #Writing RawPDOS
            with paropen(struct+'-2-Result-RawPDOS-Up.csv', "w") as fd:
                print("Energy, s-total, p-total, px, py, pz, d-total, dxy, dyz, d3z2_r2, dzx, dx2_y2, f-total, TOTAL", file=fd)
                for j in range(0, bulk_configuration.get_global_number_of_atoms()):
                    print("Atom no: "+str(j+1)+", Atom Symbol: "+chem_sym[j]+" --------------------", file=fd)
                    pdoss = rawdos.raw_pdos(energies, a=j, l=0, m=None, spin=1, width=DOS_width)
                    pdosp = rawdos.raw_pdos(energies, a=j, l=1, m=None, spin=1, width=DOS_width)
                    pdospx = rawdos.raw_pdos(energies, a=j, l=1, m=2, spin=1, width=DOS_width)
                    pdospy = rawdos.raw_pdos(energies, a=j, l=1, m=0, spin=1, width=DOS_width)
                    pdospz = rawdos.raw_pdos(energies, a=j, l=1, m=1, spin=1, width=DOS_width)
                    pdosd = rawdos.raw_pdos(energies, a=j, l=2, m=None, spin=1, width=DOS_width)
                    pdosdxy = rawdos.raw_pdos(energies, a=j, l=2, m=0, spin=1, width=DOS_width)
                    pdosdyz = rawdos.raw_pdos(energies, a=j, l=2, m=1, spin=1, width=DOS_width)
                    pdosd3z2_r2 = rawdos.raw_pdos(energies, a=j, l=2, m=2, spin=1, width=DOS_width)
                    pdosdzx = rawdos.raw_pdos(energies, a=j, l=2, m=3, spin=1, width=DOS_width)
                    pdosdx2_y2 = rawdos.raw_pdos(energies, a=j, l=2, m=4, spin=1, width=DOS_width)
                    pdosf = rawdos.raw_pdos(energies, a=j, l=3, m=None, spin=1, width=DOS_width)
                    dosspdf = pdoss + pdosp + pdosd + pdosf
                    totaldosweightsup = totaldosweightsup + dosspdf
                    for x in zip(energies, pdoss, pdosp, pdospx, pdospy, pdospz, pdosd, pdosdxy, pdosdyz, pdosd3z2_r2, pdosdzx, pdosdx2_y2, pdosf, dosspdf):
                        print(*x, sep=", ", file=fd)
                        
            # Writing DOS
            with paropen(struct+'-2-Result-DOS-Up.csv', "w") as fd:
                for x in zip(energies, totaldosweightsup):
                    print(*x, sep=", ", file=fd)

        else:

            # RAW PDOS  
            parprint("Calculating and saving Raw PDOS...")
            rawdos = DOSCalculator.from_calculator(struct+'-1-Result-Ground.gpw',soc=False, theta=0.0, phi=0.0, shift_fermi_level=True)
            energies = rawdos.get_energies(npoints=DOS_npoints)
            totaldosweights = [0.0] * DOS_npoints
            
            # Writing RawPDOS
            with paropen(struct+'-2-Result-RawPDOS.csv', "w") as fd:
                print("Energy, s-total, p-total, px, py, pz, d-total, dxy, dyz, d3z2_r2, dzx, dx2_y2, f-total, TOTAL", file=fd)
                for j in range(0, bulk_configuration.get_global_number_of_atoms()):
                    print("Atom no: "+str(j+1)+", Atom Symbol: "+chem_sym[j]+" --------------------", file=fd)
                    pdoss = rawdos.raw_pdos(energies, a=j, l=0, m=None, spin=None, width=DOS_width)
                    pdosp = rawdos.raw_pdos(energies, a=j, l=1, m=None, spin=None, width=DOS_width)
                    pdospx = rawdos.raw_pdos(energies, a=j, l=1, m=2, spin=None, width=DOS_width)
                    pdospy = rawdos.raw_pdos(energies, a=j, l=1, m=0, spin=None, width=DOS_width)
                    pdospz = rawdos.raw_pdos(energies, a=j, l=1, m=1, spin=None, width=DOS_width)
                    pdosd = rawdos.raw_pdos(energies, a=j, l=2, m=None, spin=None, width=DOS_width)
                    pdosdxy = rawdos.raw_pdos(energies, a=j, l=2, m=0, spin=None, width=DOS_width)
                    pdosdyz = rawdos.raw_pdos(energies, a=j, l=2, m=1, spin=None, width=DOS_width)
                    pdosd3z2_r2 = rawdos.raw_pdos(energies, a=j, l=2, m=2, spin=None, width=DOS_width)
                    pdosdzx = rawdos.raw_pdos(energies, a=j, l=2, m=3, spin=None, width=DOS_width)
                    pdosdx2_y2 = rawdos.raw_pdos(energies, a=j, l=2, m=4, spin=None, width=DOS_width)
                    pdosf = rawdos.raw_pdos(energies, a=j, l=3, m=None, spin=None, width=DOS_width)
                    dosspdf = pdoss + pdosp + pdosd + pdosf
                    totaldosweights = totaldosweights + dosspdf
                    for x in zip(energies, pdoss, pdosp, pdospx, pdospy, pdospz, pdosd, pdosdxy, pdosdyz, pdosd3z2_r2, pdosdzx, pdosdx2_y2, pdosf, dosspdf):
                        print(*x, sep=", ", file=fd)

            # Writing DOS
            with paropen(struct+'-2-Result-DOS.csv', "w") as fd:
                for x in zip(energies, totaldosweights):
                    print(*x, sep=", ", file=fd)
        # Finish DOS calc
        time22 = time.time()
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('DOS calculation: ', round((time22-time21),2), end="\n", file=f1)

        # Write or draw figures
        if drawfigs == True:
            # Draw graphs only on master node
            if world.rank == 0:
                # DOS
                if Spin_calc == True:
                    ax = plt.gca()
                    ax.plot(energies, -1.0*totaldosweightsdown, 'y')
                    ax.plot(energies, totaldosweightsup, 'b')
                    ax.set_xlabel('Energy [eV]')
                    ax.set_ylabel('DOS [1/eV]')
                else:
                    ax = plt.gca()
                    ax.plot(energies, totaldosweights, 'b')
                    ax.set_xlabel('Energy [eV]')
                    ax.set_ylabel('DOS [1/eV]')
                plt.xlim(Energy_min, Energy_max)
                plt.savefig(struct+'-2-Graph-DOS.png', dpi=300)
                #plt.show()
        else:
            # Draw graphs only on master node
            if world.rank == 0:
                # DOS
                if Spin_calc == True:
                    ax = plt.gca()
                    ax.plot(energies, -1.0*totaldosweightsdown, 'y')
                    ax.plot(energies, totaldosweightsup, 'b')
                    ax.set_xlabel('Energy [eV]')
                    ax.set_ylabel('DOS [1/eV]')
                else:
                    ax = plt.gca()
                    ax.plot(energies, totaldosweights, 'b')
                    ax.set_xlabel('Energy [eV]')
                    ax.set_ylabel('DOS [1/eV]')
                plt.xlim(Energy_min, Energy_max)
                plt.savefig(struct+'-2-Graph-DOS.png', dpi=300)

    def bandcalc(self, drawfigs = False):
        """
        This method performs band structure calculations for the given structure using the
        ground state results. It computes the electronic band structure along specified
        k-point paths and saves the results in appropriate files for further analysis
        and visualization.
        """

        # -------------------------------------------------------------
        # Step 3 - BAND STRUCTURE CALCULATION
        # -------------------------------------------------------------

        # Start Band calc
        time31 = time.time()
        parprint("Starting band structure calculation...")
        if Mode == 'PW-GW':      
            GW = GWBands(calc=struct+'-1-Result-Ground.gpw', fixdensity=True,
                 gw_file=struct+'-1-_results.pckl',kpoints=GW_kpoints_list)

            # Getting results without spin-orbit
            results = GW.get_gw_bands(SO=False, interpolate=GW_interpolate_band, vac=True)

            # Extracting data
            X = results['X']
            ef = results['ef']
            xdata = results['x_k']
            banddata = results['e_kn']

            np.savetxt(struct+'-3-Result-Band.dat', np.c_[xdata,banddata])

            with open(struct+'-3-Result-Band.dat', 'a') as f:
                print ('Symmetry points: ', X, end="\n", file=f)
                print ('Fermi Level: ', ef, end="\n", file=f)

        else:
            if XC_calc in ['HSE06', 'HSE03']:
                calc = GPAW(struct+'-1-Result-Ground.gpw',
                        parallel={'band': 1, 'kpt': 1}, 
                        txt=struct+'-3-Log-Band.txt',
                        symmetry='off', occupations = Occupation,
                        kpts={'path': Band_path, 'npoints': Band_npoints}, convergence=Band_convergence)
                
            else:
                calc = GPAW(struct+'-1-Result-Ground.gpw',
                        txt=struct+'-3-Log-Band.txt',
                        fixdensity=True,
                        symmetry='off', occupations = Occupation,
                        kpts={'path': Band_path, 'npoints': Band_npoints},
                        convergence=Band_convergence)

            calc.get_potential_energy()
            bs = calc.band_structure()
            ef = calc.get_fermi_level()
            Band_num_of_bands = calc.get_number_of_bands()
            parprint('Num of bands:'+str(Band_num_of_bands))

            # No need to write an additional gpaw file. Use json file to use with ase band-structure command
            #calc.write(struct+'-3-Result-Band.gpw')
            bs.write(struct+'-3-Result-Band.json')

            if Spin_calc == True:
                eps_skn = np.array([[calc.get_eigenvalues(k,s)
                                    for k in range(Band_npoints)]
                                    for s in range(2)]) - ef
                parprint(eps_skn.shape)
                with paropen(struct+'-3-Result-Band-Down.dat', 'w') as f1:
                    for n1 in range(Band_num_of_bands):
                        for k1 in range(Band_npoints):
                            print(k1, eps_skn[0, k1, n1], end="\n", file=f1)
                        print (end="\n", file=f1)

                with paropen(struct+'-3-Result-Band-Up.dat', 'w') as f2:
                    for n2 in range(Band_num_of_bands):
                        for k2 in range(Band_npoints):
                            print(k2, eps_skn[1, k2, n2], end="\n", file=f2)
                        print (end="\n", file=f2)
                
                # Thanks to Andrej Kesely (https://stackoverflow.com/users/10035985/andrej-kesely) for helping the problem of general XYYY writer
                currentd, all_groupsd = [], []
                with open(struct+'-3-Result-Band-Down.dat', 'r') as f_in1:
                    for line in map(str.strip, f_in1):
                        if line == "" and currentd:
                            all_groupsd.append(currentd)
                            currentd = []
                        else:
                            currentd.append(line.split(maxsplit=1))

                if currentd:
                    all_groupsd.append(currentd)

                with paropen(struct+'-3-Result-Band-Down-XYYY.dat', 'w') as f1:
                    for g in zip(*all_groupsd):
                        print('{} {} {}'.format(g[0][0], g[0][1], ' '.join(v for _, v in g[1:])), file=f1)
                
                currentu, all_groupsu = [], []
                with open(struct+'-3-Result-Band-Up.dat', 'r') as f_in2:
                    for line in map(str.strip, f_in2):
                        if line == "" and currentu:
                            all_groupsu.append(currentu)
                            currentu = []
                        else:
                            currentu.append(line.split(maxsplit=1))

                if currentu:
                    all_groupsu.append(currentu)

                with paropen(struct+'-3-Result-Band-Up-XYYY.dat', 'w') as f2:
                    for g in zip(*all_groupsu):
                        print('{} {} {}'.format(g[0][0], g[0][1], ' '.join(v for _, v in g[1:])), file=f2)

            else:
                eps_skn = np.array([[calc.get_eigenvalues(k,s)
                                    for k in range(Band_npoints)]
                                    for s in range(1)]) - ef
                with paropen(struct+'-3-Result-Band.dat', 'w') as f:
                    for n in range(Band_num_of_bands):
                        for k in range(Band_npoints):
                            print(k, eps_skn[0, k, n], end="\n", file=f)
                        print (end="\n", file=f)
                        

                # Thanks to Andrej Kesely (https://stackoverflow.com/users/10035985/andrej-kesely) for helping the problem of general XYYY writer
                current, all_groups = [], []
                with open(struct+'-3-Result-Band.dat', 'r') as f_in:
                    for line in map(str.strip, f_in):
                        if line == "" and current:
                            all_groups.append(current)
                            current = []
                        else:
                            current.append(line.split(maxsplit=1))

                if current:
                    all_groups.append(current)

                with paropen(struct+'-3-Result-Band-XYYY.dat', 'w') as f1:
                    for g in zip(*all_groups):
                        print('{} {} {}'.format(g[0][0], g[0][1], ' '.join(v for _, v in g[1:])), file=f1)
    
        # Finish Band calc
        time32 = time.time()
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('Band calculation: ', round((time32-time31),2), end="\n", file=f1)

        # Write or draw figures
        if drawfigs == True:
            # Draw graphs only on master node
            if world.rank == 0:
                # Band Structure
                if Mode == 'PW-GW':
                    f = plt.figure()
                    plt.plot(xdata, banddata, '-b', '-r', linewidth=1)
                    plt.xticks(X, GW_kpoints_list, fontsize=8)
                    plt.ylabel('Energy with respect to vacuum (eV)', fontsize=14)
                    plt.tight_layout()
                    plt.savefig(struct+'-3-Graph-Band.png', dpi=300)
                    plt.show()
                else:
                    bs.plot(filename=struct+'-3-Graph-Band.png', show=True, emax=Energy_max, emin=Energy_min)
        else:
            # Draw graphs only on master node
            if world.rank == 0:
                # Band Structure
                if Mode == 'PW-GW':
                    f = plt.figure()
                    plt.plot(xdata, banddata, '-b', '-r', linewidth=1)
                    plt.xticks(X, GW_kpoints_list, fontsize=8)
                    plt.ylabel('Energy with respect to vacuum (eV)', fontsize=14)
                    plt.tight_layout()
                    plt.savefig(struct+'-3-Graph-Band.png', dpi=300)
                    #plt.show()
                else:
                    bs.plot(filename=struct+'-3-Graph-Band.png', show=False, emax=Energy_max, emin=Energy_min)

    def densitycalc(self):
        """
        This method performs density calculations for the given structure using the
        ground state results. It computes the electron density distribution and saves
        the results in appropriate files for further analysis and visualization.
        """

        # -------------------------------------------------------------
        # Step 4 - ALL-ELECTRON DENSITY
        # -------------------------------------------------------------
        
        #Start Density calc
        time41 = time.time()
        parprint("Starting All-electron density calculation...")
        calc = GPAW(struct+'-1-Result-Ground.gpw', txt=struct+'-4-Log-ElectronDensity.txt')
        bulk_configuration.calc = calc
        np = calc.get_pseudo_density()
        n = calc.get_all_electron_density(gridrefinement=Refine_grid)
        
        # Writing pseudo and all electron densities to cube file with Bohr unit
        write(struct+'-4-Result-All-electron_nall.cube', bulk_configuration, data=n * Bohr**3)
        write(struct+'-4-Result-All-electron_npseudo.cube', bulk_configuration, data=np * Bohr**3)
        # Finish Density calc
        time42 = time.time()
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('Density calculation: ', round((time42-time41),2), end="\n", file=f1)

    def phononcalc(self):
        """
        This method performs a phonon calculation for the given structure using the ground state results. 
        It generates atomic displacements, computes force constants, and calculates phonon dispersion and phonon DOS.
        The results are saved as PNG file for now.
        """
        # -------------------------------------------------------------
        # Step 5 - PHONON CALCULATION
        # -------------------------------------------------------------
        
        time51 = time.time()
        parprint("Starting phonon calculation.(\033[93mWARNING:\033[0mNOT TESTED FEATURE, PLEASE CONTROL THE RESULTS)")
        
        calc = GPAW(struct+'-1-Result-Ground.gpw')
        bulk_configuration.calc = calc
    
        # Pre-process
        bulk_configuration_ph = convert_atoms_to_phonopy(bulk_configuration)
        phonon = Phonopy(bulk_configuration_ph, Phonon_supercell, log_level=1)
        phonon.generate_displacements(distance=Phonon_displacement)
        with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
            print("[Phonopy] Atomic displacements:", end="\n", file=f2)
            disps = phonon.get_displacements()
            for d in disps:
                print("[Phonopy] %d %s" % (d[0], d[1:]), end="\n", file=f2)

        # FIX THIS PART
        calc = GPAW(mode=PW(Phonon_PW_cutoff),
               kpts={'size': (Phonon_kpts_x, Phonon_kpts_y, Phonon_kpts_z)}, txt=struct+'-5-Log-Phonon-GPAW.txt')
        
        bulk_configuration.calc = calc
        
        path = get_band_path(bulk_configuration, Phonon_path, Phonon_npoints)

        phonon_path = struct+'5-Results-force-constants.npy'
        sum_rule=Phonon_acoustic_sum_rule

        if os.path.exists(phonon_path):
            with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
                print('Reading FCs from {!r}'.format(phonon_path), end="\n", file=f2)
            phonon.force_constants = np.load(phonon_path)

        else:
            with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
                print('Computing FCs',end="\n", file=f2)
                #os.makedirs('force-sets', exist_ok=True)
            supercells = list(phonon.get_supercells_with_displacements())
            fnames = [struct+'5-Results-sc-{:04}.npy'.format(i) for i in range(len(supercells))]
            set_of_forces = [
                load_or_compute_force(fname, calc, supercell)
                for (fname, supercell) in zip(fnames, supercells)
            ]
            with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
                print('Building FC matrix', end="\n", file=f2)
            phonon.produce_force_constants(forces=set_of_forces, calculate_full_force_constants=False)
            if sum_rule:
                phonon.symmetrize_force_constants()
            with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
                print('Writing FCs to {!r}'.format(phonon_path), end="\n", file=f2)
            np.save(phonon_path, phonon.get_force_constants())
            #shutil.rmtree('force-sets')

        with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
            print('', end="\n", file=f2)
            print("[Phonopy] Phonon frequencies at Gamma:", end="\n", file=f2)
            for i, freq in enumerate(phonon.get_frequencies((0, 0, 0))):
                print("[Phonopy] %3d: %10.5f THz" %  (i + 1, freq), end="\n", file=f2) # THz

            # DOS
            phonon.set_mesh([21, 21, 21])
            phonon.set_total_DOS(tetrahedron_method=True)
            print('', end="\n", file=f2)
            print("[Phonopy] Phonon DOS:", end="\n", file=f2)
            for omega, dos in np.array(phonon.get_total_DOS()).T:
                print("%15.7f%15.7f" % (omega, dos), end="\n", file=f2)

        qpoints, labels, connections = path
        phonon.run_band_structure(qpoints, path_connections=connections, labels=labels)

        # without DOS
        # fig = phonon.plot_band_structure()
        
        # with DOS
        phonon.run_mesh([20, 20, 20])
        phonon.run_total_dos()
        fig = phonon.plot_band_structure_and_dos()

        # with PDOS
        # phonon.run_mesh([20, 20, 20], with_eigenvectors=True, is_mesh_symmetry=False)
        # fig = phonon.plot_band_structure_and_dos(pdoc_indices=[[0], [1]])

        fig.savefig(struct+'-5-Result-Phonon.png', dpi=300)

        time52 = time.time()
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('Phonon calculation: ', round((time52-time51),2), end="\n", file=f1)
            
    
    def opticalcalc(self):
        """
        This method performs optical property calculations for the given structure using the
        ground state results. It computes the dielectric function, absorption spectrum, and
        other related optical properties. The results are saved in appropriate files for
        further analysis and visualization.
        """

        # -------------------------------------------------------------
        # Step 6 - OPTICAL CALCULATION
        # -------------------------------------------------------------
        
        #Start Optical calc
        time61 = time.time()
        if Mode == 'PW':
            parprint("Starting optical calculation...")
            try:
                calc = GPAW(struct+'-1-Result-Ground.gpw',
                        txt=struct+'-6-Log-Optical.txt',
                        nbands=Opt_num_of_bands,
                        fixdensity=True,
                        symmetry='off',
                        occupations=FermiDirac(Opt_FD_smearing))
            except FileNotFoundError as err:
                # output error, and return with an error code
                parprint('\033[91mERROR:\033[0mOptical computations must be done separately. Please do ground calculations first.')
                quit()
        
            calc.get_potential_energy()

            calc.diagonalize_full_hamiltonian(nbands=Opt_num_of_bands)  # diagonalize Hamiltonian
            calc.write(struct+'-6-Result-Optical.gpw', 'all')  # write wavefunctions

            #from mpi4py import MPI
            if Opt_calc_type == 'BSE':
                if Spin_calc == True:
                   parprint('\033[91mERROR:\033[0mBSE calculations can not run with spin dependent data.')
                   quit()
                parprint('Starting BSE calculations')
                bse = BSE(calc= struct+'-6-Result-Optical.gpw', ecut=Opt_cut_of_energy,
                             valence_bands=Opt_BSE_valence,
                             conduction_bands=Opt_BSE_conduction,
                             nbands=Opt_num_of_bands,
                             eshift=Opt_shift_en,
                             mode='BSE',
                             write_v=True,
                             integrate_gamma=0,
                             txt=struct+'-6-Log-Optical-BSE.txt')
                
                # Getting dielectric function spectrum
                parprint("Starting dielectric function calculation...")
                # Writing to files
                bse.get_dielectric_function(direction=0, q_c = [0.0, 0.0, 0.0], eta=Opt_eta,
                                            w_w=np.linspace(Opt_BSE_min_en, Opt_BSE_max_en, Opt_BSE_num_of_data),
                                            filename=struct+'-6-Result-Optical-BSE_dielec_xdirection.csv',
                                            write_eig=struct+'-6-Result-Optical-BSE_eig_xdirection.dat')
                bse.get_dielectric_function(direction=1, q_c = [0.0, 0.0, 0.0], eta=Opt_eta,
                                            w_w=np.linspace(Opt_BSE_min_en, Opt_BSE_max_en, Opt_BSE_num_of_data),
                                            filename=struct+'-6-Result-Optical-BSE_dielec_ydirection.csv',
                                            write_eig=struct+'-6-Result-Optical-BSE_eig_ydirection.dat')
                bse.get_dielectric_function(direction=2, q_c = [0.0, 0.0, 0.0], eta=Opt_eta,
                                            w_w=np.linspace(Opt_BSE_min_en, Opt_BSE_max_en, Opt_BSE_num_of_data),
                                            filename=struct+'-6-Result-Optical-BSE_dielec_zdirection.csv',
                                            write_eig=struct+'-6-Result-Optical-BSE_eig_zdirection.dat')
                                            
                # Loading dielectric function spectrum to numpy
                dielec_x = genfromtxt(struct+'-6-Result-Optical-BSE_dielec_xdirection.csv', delimiter=',')
                dielec_y = genfromtxt(struct+'-6-Result-Optical-BSE_dielec_ydirection.csv', delimiter=',')
                dielec_z = genfromtxt(struct+'-6-Result-Optical-BSE_dielec_zdirection.csv', delimiter=',')
                # dielec_x.shape[0] will give us the length of data.
                # c and h
                c_opt = 29979245800
                h_opt = 6.58E-16
                #c_opt = 1
                #h_opt = 1

                # Initialize arrays
                opt_n_bse_x = np.array ([1e-6,]*dielec_x.shape[0])
                opt_k_bse_x = np.array ([1e-6,]*dielec_x.shape[0])
                opt_abs_bse_x = np.array([1e-6,]*dielec_x.shape[0])
                opt_ref_bse_x = np.array([1e-6,]*dielec_x.shape[0])
                opt_n_bse_y = np.array ([1e-6,]*dielec_y.shape[0])
                opt_k_bse_y = np.array ([1e-6,]*dielec_y.shape[0])
                opt_abs_bse_y = np.array([1e-6,]*dielec_y.shape[0])
                opt_ref_bse_y = np.array([1e-6,]*dielec_y.shape[0])
                opt_n_bse_z = np.array ([1e-6,]*dielec_z.shape[0])
                opt_k_bse_z = np.array ([1e-6,]*dielec_z.shape[0])
                opt_abs_bse_z = np.array([1e-6,]*dielec_z.shape[0])
                opt_ref_bse_z = np.array([1e-6,]*dielec_z.shape[0])

                # Calculation of other optical data
                for n in range(dielec_x.shape[0]):
                    # x-direction
                    opt_n_bse_x[n] = np.sqrt((np.sqrt(np.square(dielec_x[n][1])+np.square(dielec_x[n][2]))+dielec_x[n][1])/2.0)
                    opt_k_bse_x[n] = np.sqrt((np.sqrt(np.square(dielec_x[n][1])+np.square(dielec_x[n][2]))-dielec_x[n][1])/2.0)
                    opt_abs_bse_x[n] = 2*dielec_x[n][0]*opt_k_bse_x[n]/(h_opt*c_opt)
                    opt_ref_bse_x[n] = (np.square(1-opt_n_bse_x[n])+np.square(opt_k_bse_x[n]))/(np.square(1+opt_n_bse_x[n])+np.square(opt_k_bse_x[n]))
                    # y-direction
                    opt_n_bse_y[n] = np.sqrt((np.sqrt(np.square(dielec_y[n][1])+np.square(dielec_y[n][2]))+dielec_y[n][1])/2.0)
                    opt_k_bse_y[n] = np.sqrt((np.sqrt(np.square(dielec_y[n][1])+np.square(dielec_y[n][2]))-dielec_y[n][1])/2.0)
                    opt_abs_bse_y[n] = 2*dielec_y[n][0]*opt_k_bse_y[n]/(h_opt*c_opt)
                    opt_ref_bse_y[n] = (np.square(1-opt_n_bse_y[n])+np.square(opt_k_bse_y[n]))/(np.square(1+opt_n_bse_y[n])+np.square(opt_k_bse_y[n]))
                    # z-direction
                    opt_n_bse_z[n] = np.sqrt((np.sqrt(np.square(dielec_z[n][1])+np.square(dielec_z[n][2]))+dielec_z[n][1])/2.0)
                    opt_k_bse_z[n] = np.sqrt((np.sqrt(np.square(dielec_z[n][1])+np.square(dielec_z[n][2]))-dielec_z[n][1])/2.0)
                    opt_abs_bse_z[n] = 2*dielec_z[n][0]*opt_k_bse_z[n]/(h_opt*c_opt)
                    opt_ref_bse_z[n] = (np.square(1-opt_n_bse_z[n])+np.square(opt_k_bse_z[n]))/(np.square(1+opt_n_bse_z[n])+np.square(opt_k_bse_z[n]))

                # Saving other data for x-direction
                with paropen(struct+'-6-Result-Optical-BSE-AllData_xdirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_x.shape[0]):
                        print(dielec_x[n][0], dielec_x[n][1], dielec_x[n][2], opt_n_bse_x[n], opt_k_bse_x[n], opt_abs_bse_x[n], opt_ref_bse_x[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # Saving other data for y-direction
                with paropen(struct+'-6-Result-Optical-BSE-AllData_ydirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_y.shape[0]):
                        print(dielec_y[n][0], dielec_y[n][1], dielec_y[n][2], opt_n_bse_y[n], opt_k_bse_y[n], opt_abs_bse_y[n], opt_ref_bse_y[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # Saving other data for z-direction
                with paropen(struct+'-6-Result-Optical-BSE-AllData_zdirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_z.shape[0]):
                        print(dielec_z[n][0], dielec_z[n][1], dielec_z[n][2], opt_n_bse_z[n], opt_k_bse_z[n], opt_abs_bse_z[n], opt_ref_bse_z[n], end="\n", file=f1)
                    print (end="\n", file=f1)

            elif Opt_calc_type == 'RPA':
                parprint('Starting RPA calculations')
                df = DielectricFunction(calc=struct+'-6-Result-Optical.gpw',
                                    eta=Opt_eta, nblocks=Opt_nblocks,
                                    omega2=Opt_omega2,
                                    domega0=Opt_domega0,
                                    ecut=Opt_cut_of_energy)
                # Writing to files as: omega, nlfc.real, nlfc.imag, lfc.real, lfc.imag 
                # Here lfc is local field correction
                # Getting dielectric function spectrum
                parprint("Starting dielectric function calculation...")
                df.get_dielectric_function( direction='x', 
                                            filename=struct+'-6-Result-Optical-RPA_dielec_xdirection.csv')
                df.get_dielectric_function( direction='y',
                                            filename=struct+'-6-Result-Optical-RPA_dielec_ydirection.csv')
                df.get_dielectric_function( direction='z',
                                            filename=struct+'-6-Result-Optical-RPA_dielec_zdirection.csv')

                # Loading dielectric function spectrum to numpy
                dielec_x = genfromtxt(struct+'-6-Result-Optical-RPA_dielec_xdirection.csv', delimiter=',')
                dielec_y = genfromtxt(struct+'-6-Result-Optical-RPA_dielec_ydirection.csv', delimiter=',')
                dielec_z = genfromtxt(struct+'-6-Result-Optical-RPA_dielec_zdirection.csv', delimiter=',')
                # dielec_x.shape[0] will give us the length of data.
                # c and h
                c_opt = 29979245800
                h_opt = 6.58E-16
                #c_opt = 1
                #h_opt = 1
                # ---- NLFC ----
                # Initialize arrays for NLFC
                opt_n_nlfc_x = np.array ([1e-6,]*dielec_x.shape[0])
                opt_k_nlfc_x = np.array ([1e-6,]*dielec_x.shape[0])
                opt_abs_nlfc_x = np.array([1e-6,]*dielec_x.shape[0])
                opt_ref_nlfc_x = np.array([1e-6,]*dielec_x.shape[0])
                opt_n_nlfc_y = np.array ([1e-6,]*dielec_y.shape[0])
                opt_k_nlfc_y = np.array ([1e-6,]*dielec_y.shape[0])
                opt_abs_nlfc_y = np.array([1e-6,]*dielec_y.shape[0])
                opt_ref_nlfc_y = np.array([1e-6,]*dielec_y.shape[0])
                opt_n_nlfc_z = np.array ([1e-6,]*dielec_z.shape[0])
                opt_k_nlfc_z = np.array ([1e-6,]*dielec_z.shape[0])
                opt_abs_nlfc_z = np.array([1e-6,]*dielec_z.shape[0])
                opt_ref_nlfc_z = np.array([1e-6,]*dielec_z.shape[0])

                # Calculation of other optical spectrum for NLFC
                for n in range(dielec_x.shape[0]):
                    # NLFC-x
                    opt_n_nlfc_x[n] = np.sqrt((np.sqrt(np.square(dielec_x[n][1])+np.square(dielec_x[n][2]))+dielec_x[n][1])/2.0)
                    opt_k_nlfc_x[n] = np.sqrt((np.sqrt(np.square(dielec_x[n][1])+np.square(dielec_x[n][2]))-dielec_x[n][1])/2.0)
                    opt_abs_nlfc_x[n] = 2*dielec_x[n][0]*opt_k_nlfc_x[n]/(h_opt*c_opt)
                    opt_ref_nlfc_x[n] = (np.square(1-opt_n_nlfc_x[n])+np.square(opt_k_nlfc_x[n]))/(np.square(1+opt_n_nlfc_x[n])+np.square(opt_k_nlfc_x[n]))
                    # NLFC-y
                    opt_n_nlfc_y[n] = np.sqrt((np.sqrt(np.square(dielec_y[n][1])+np.square(dielec_y[n][2]))+dielec_y[n][1])/2.0)
                    opt_k_nlfc_y[n] = np.sqrt((np.sqrt(np.square(dielec_y[n][1])+np.square(dielec_y[n][2]))-dielec_y[n][1])/2.0)
                    opt_abs_nlfc_y[n] = 2*dielec_y[n][0]*opt_k_nlfc_y[n]/(h_opt*c_opt)
                    opt_ref_nlfc_y[n] = (np.square(1-opt_n_nlfc_y[n])+np.square(opt_k_nlfc_y[n]))/(np.square(1+opt_n_nlfc_y[n])+np.square(opt_k_nlfc_y[n]))
                    # NLFC-z
                    opt_n_nlfc_z[n] = np.sqrt((np.sqrt(np.square(dielec_z[n][1])+np.square(dielec_z[n][2]))+dielec_z[n][1])/2.0)
                    opt_k_nlfc_z[n] = np.sqrt((np.sqrt(np.square(dielec_z[n][1])+np.square(dielec_z[n][2]))-dielec_z[n][1])/2.0)
                    opt_abs_nlfc_z[n] = 2*dielec_z[n][0]*opt_k_nlfc_z[n]/(h_opt*c_opt)
                    opt_ref_nlfc_z[n] = (np.square(1-opt_n_nlfc_z[n])+np.square(opt_k_nlfc_z[n]))/(np.square(1+opt_n_nlfc_z[n])+np.square(opt_k_nlfc_z[n]))

                # Saving NLFC other optical spectrum for x-direction
                with paropen(struct+'-6-Result-Optical-RPA-NLFC-AllData_xdirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_x.shape[0]):
                        print(dielec_x[n][0], dielec_x[n][1], dielec_x[n][2], opt_n_nlfc_x[n], opt_k_nlfc_x[n], opt_abs_nlfc_x[n], opt_ref_nlfc_x[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # Saving NLFC other optical spectrum for y-direction
                with paropen(struct+'-6-Result-Optical-RPA-NLFC-AllData_ydirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_y.shape[0]):
                        print(dielec_y[n][0], dielec_y[n][1], dielec_y[n][2], opt_n_nlfc_y[n], opt_k_nlfc_y[n], opt_abs_nlfc_y[n], opt_ref_nlfc_y[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # Saving NLFC other optical spectrum for z-direction
                with paropen(struct+'-6-Result-Optical-RPA-NLFC-AllData_zdirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_z.shape[0]):
                        print(dielec_z[n][0], dielec_z[n][1], dielec_z[n][2], opt_n_nlfc_z[n], opt_k_nlfc_z[n], opt_abs_nlfc_z[n], opt_ref_nlfc_z[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # ---- LFC ----
                # Initialize arrays for LFC
                opt_n_lfc_x = np.array ([1e-6,]*dielec_x.shape[0])
                opt_k_lfc_x = np.array ([1e-6,]*dielec_x.shape[0])
                opt_abs_lfc_x = np.array([1e-6,]*dielec_x.shape[0])
                opt_ref_lfc_x = np.array([1e-6,]*dielec_x.shape[0])
                opt_n_lfc_y = np.array ([1e-6,]*dielec_y.shape[0])
                opt_k_lfc_y = np.array ([1e-6,]*dielec_y.shape[0])
                opt_abs_lfc_y = np.array([1e-6,]*dielec_y.shape[0])
                opt_ref_lfc_y = np.array([1e-6,]*dielec_y.shape[0])
                opt_n_lfc_z = np.array ([1e-6,]*dielec_z.shape[0])
                opt_k_lfc_z = np.array ([1e-6,]*dielec_z.shape[0])
                opt_abs_lfc_z = np.array([1e-6,]*dielec_z.shape[0])
                opt_ref_lfc_z = np.array([1e-6,]*dielec_z.shape[0])

                # Calculation of other optical spectrum for LFC
                for n in range(dielec_x.shape[0]):
                    # LFC-x
                    opt_n_lfc_x[n] = np.sqrt((np.sqrt(np.square(dielec_x[n][3])+np.square(dielec_x[n][4]))+dielec_x[n][3])/2.0)
                    opt_k_lfc_x[n] = np.sqrt((np.sqrt(np.square(dielec_x[n][3])+np.square(dielec_x[n][4]))-dielec_x[n][3])/2.0)
                    opt_abs_lfc_x[n] = 2*dielec_x[n][0]*opt_k_nlfc_x[n]/(h_opt*c_opt)
                    opt_ref_lfc_x[n] = (np.square(1-opt_n_lfc_x[n])+np.square(opt_k_lfc_x[n]))/(np.square(1+opt_n_lfc_x[n])+np.square(opt_k_lfc_x[n]))
                    # LFC-y
                    opt_n_lfc_y[n] = np.sqrt((np.sqrt(np.square(dielec_y[n][3])+np.square(dielec_y[n][4]))+dielec_y[n][3])/2.0)
                    opt_k_lfc_y[n] = np.sqrt((np.sqrt(np.square(dielec_y[n][3])+np.square(dielec_y[n][4]))-dielec_y[n][3])/2.0)
                    opt_abs_lfc_y[n] = 2*dielec_y[n][0]*opt_k_lfc_y[n]/(h_opt*c_opt)
                    opt_ref_lfc_y[n] = (np.square(1-opt_n_lfc_y[n])+np.square(opt_k_lfc_y[n]))/(np.square(1+opt_n_lfc_y[n])+np.square(opt_k_lfc_y[n]))
                    # LFC-z
                    opt_n_lfc_z[n] = np.sqrt((np.sqrt(np.square(dielec_z[n][3])+np.square(dielec_z[n][4]))+dielec_z[n][3])/2.0)
                    opt_k_lfc_z[n] = np.sqrt((np.sqrt(np.square(dielec_z[n][3])+np.square(dielec_z[n][4]))-dielec_z[n][3])/2.0)
                    opt_abs_lfc_z[n] = 2*dielec_z[n][0]*opt_k_lfc_z[n]/(h_opt*c_opt)
                    opt_ref_lfc_z[n] = (np.square(1-opt_n_lfc_z[n])+np.square(opt_k_lfc_z[n]))/(np.square(1+opt_n_lfc_z[n])+np.square(opt_k_lfc_z[n]))

                # Saving LFC other optical spectrum for x-direction
                with paropen(struct+'-6-Result-Optical-RPA-LFC-AllData_xdirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_x.shape[0]):
                        print(dielec_x[n][0], dielec_x[n][3], dielec_x[n][4], opt_n_lfc_x[n], opt_k_lfc_x[n], opt_abs_lfc_x[n], opt_ref_lfc_x[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # Saving LFC other optical spectrum for y-direction
                with paropen(struct+'-6-Result-Optical-RPA-LFC-AllData_ydirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_y.shape[0]):
                        print(dielec_y[n][0], dielec_y[n][3], dielec_y[n][4], opt_n_lfc_y[n], opt_k_lfc_y[n], opt_abs_lfc_y[n], opt_ref_lfc_y[n], end="\n", file=f1)
                    print (end="\n", file=f1)

                # Saving LFC other optical spectrum for z-direction
                with paropen(struct+'-6-Result-Optical-RPA-LFC-AllData_zdirection.dat', 'w') as f1:
                    print("Energy(eV) Eps_real Eps_img Refractive_Index Extinction_Index Absorption(1/cm) Reflectivity", end="\n", file=f1)
                    for n in range(dielec_z.shape[0]):
                        print(dielec_z[n][0], dielec_z[n][3], dielec_z[n][4], opt_n_lfc_z[n], opt_k_lfc_z[n], opt_abs_lfc_z[n], opt_ref_lfc_z[n], end="\n", file=f1)
                    print (end="\n", file=f1)
                
            else:
                parprint('\033[91mERROR:\033[0mUnknown optical calculation type.')
                quit()

        elif Mode == 'LCAO':
            parprint('\033[91mERROR:\033[0mNot implemented in LCAO mode yet.')
        else:
            parprint('\033[91mERROR:\033[0mNot implemented in FD mode yet.')
        # Finish Optical calc
        time62 = time.time()
        # Write timings of calculation
        with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
            print('Optical calculation: ', round((time62-time61),2), end="\n", file=f1)

# Phonon related functions
# The remaining functions related to phonon calculations in this file are MIT-licensed by (C) 2020 Michael Lamparski

def get_band_path(atoms, path_str, npoints, path_frac=None, labels=None):
    from ase.dft.kpoints import bandpath

    atoms = convert_atoms_to_ase(atoms)
    if path_str is None:
        path_str = atoms.get_cell().bandpath().path

    # Commas are part of ase's supported syntax, but we'll take care of them
    # ourselves to make it easier to get things the way phonopy wants them
    if path_frac is None:
        path_frac = []
        for substr in path_str.split(','):
            path = bandpath(substr, atoms.get_cell()[...], npoints=1)
            path_frac.append(path.kpts)

    if labels is None:
        labels = []
        for substr in path_str.split(','):
            path = bandpath(substr, atoms.get_cell()[...], npoints=1)

            _, _, substr_labels = path.get_linear_kpoint_axis()
            labels.extend(['$\\Gamma$' if s == 'G' else s for s in substr_labels])

    qpoints, connections = get_band_qpoints_and_path_connections(path_frac, npoints=npoints)
    return qpoints, labels, connections

def run_gpaw_all(calc, phonon):
    return [ run_gpaw(calc, supercell) for supercell in phonon.get_supercells_with_displacements() ]

def run_gpaw(calc, cell):
    cell = convert_atoms_to_ase(cell)
    cell.set_calculator(calc)
    forces = cell.get_forces()
    drift_force = forces.sum(axis=0)
    with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
        print(("[Phonopy] Drift force:" + "%11.5f" * 3) % tuple(drift_force), end="\n", file=f2)
    # Simple translational invariance
    for force in forces:
        force -= drift_force / forces.shape[0]
    return forces

#--------------------------------------------------------------------


def load_or_compute_force(path, calc, atoms):
    if os.path.exists(path):
        with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
            print('Reading {!r}'.format(path), end="\n", file=f2)
        return np.load(path)

    else:
        with paropen(struct+'-5-Log-Phonon-Phonopy.txt', 'a') as f2:
            print('Computing {!r}'.format(path), end="\n", file=f2)
        force_set = run_gpaw(calc, atoms)
        np.save(path, force_set)
        return force_set

#--------------------------------------------------------------------

def convert_atoms_to_ase(atoms):
    return Atoms(
        symbols=atoms.get_chemical_symbols(),
        scaled_positions=atoms.get_scaled_positions(),
        cell=atoms.get_cell(),
        pbc=True
    )

def convert_atoms_to_phonopy(atoms):
    return PhonopyAtoms(
        symbols=atoms.get_chemical_symbols(),
        scaled_positions=atoms.get_scaled_positions(),
        cell=atoms.get_cell(),
        pbc=True
    )


# End of phonon related functions------------------------------

if __name__ == "__main__":
    #
    # DEFAULT VALUES
    # These values (with bulk configuration) can be used to run this script without using inputfile (py file)
    # and configuration file (cif file).
    # -------------------------------------------------------------
    Mode = 'PW'             # Use PW, PW-GW, PW-EXX, LCAO, FD  (PW is more accurate, LCAO is quicker mostly.)
    # -------------------------------------------------------------
    Geo_optim = True       # Geometric optimization with LFBGS
    Elastic_calc = False    # Elastic calculation
    DOS_calc = False         # DOS calculation
    Band_calc = False        # Band structure calculation
    Density_calc = False    # Calculate the all-electron density?
    Phonon_calc = False     # Phonon calculations
    Optical_calc = False     # Calculate the optical properties

    # -------------------------------------------------------------
    # Parameters
    # -------------------------------------------------------------
    # GEOMETRY
    Optimizer = 'QuasiNewton' # QuasiNewton, GPMin, LBFGS or FIRE
    Max_F_tolerance = 0.05 	# Maximum force tolerance in LBFGS geometry optimization. Unit is eV/Ang.
    Max_step = 0.1          # How far is a single atom allowed to move. Default is 0.2 Ang.
    Alpha = 60.0            # LBFGS only: Initial guess for the Hessian (curvature of energy surface)
    Damping = 1.0           # LBFGS only: The calculated step is multiplied with this number before added to the positions
    Fix_symmetry = False    # True for preserving the spacegroup symmetry during optimisation
    # Which components of strain will be relaxed: EpsX, EpsY, EpsZ, ShearYZ, ShearXZ, ShearXY
    # Example: For a x-y 2D nanosheet only first 2 component will be true
    Relax_cell = [False, False, False, False, False, False]

    # GROUND ----------------------
    Cut_off_energy = 340 	# eV
    #Ground_kpts_dens = 2.5     # pts per Å^-1  If the user prefers to use this, Ground_kpts_x,y,z will not be used automatically.
    Ground_kpts_x = 5 	# kpoints in x direction
    Ground_kpts_y = 5	# kpoints in y direction
    Ground_kpts_z = 5	# kpoints in z direction
    Ground_gpts_dens = 0.2     # (for LCAO) Unit is Å. If the user prefers to use this, Ground_gpts_x,y,z will not be used automatically.
    Ground_gpts_x = 8              # grid points in x direction (for LCAO)
    Ground_gpts_y = 8              # grid points in y direction (for LCAO)
    Ground_gpts_z = 8              # grid points in z direction (for LCAO)
    Setup_params = {}            # Can be used like {'N': ':p,6.0'} for Hubbard, can also be used for many corrections.https://wiki.fysik.dtu.dk/gpaw/devel/setups.html#gpaw.setup.Setup For none use {}
    XC_calc = 'LDA'         # Exchange-Correlation, choose one: LDA, PBE, GLLBSCM, HSE06, HSE03, revPBE, RPBE, PBE0(for PW-EXX)
    Ground_convergence = {}   # Convergence items for ground state calculations
    Occupation = {'name': 'fermi-dirac', 'width': 0.05}  # Refer to GPAW docs: https://wiki.fysik.dtu.dk/gpaw/documentation/basic.html#occupation-numbers
    Mixer_type = MixerSum(0.1, 3, 50) # MixerSum(beta,nmaxold, weight) default:(0.1,3,50), you can try (0.02, 5, 100) and (0.05, 5, 50)
    Spin_calc = False        # Spin polarized calculation?
    Magmom_per_atom = 1.0    # Magnetic moment per atom

    # DOS ----------------------
    DOS_npoints = 501                # Number of points
    DOS_width = 0.1                  # Width of Gaussian smearing. Use 0.0 for linear tetrahedron interpolation
    DOS_convergence = {}             # Convergence items for DOS calculations

    # BAND ----------------------
    Gamma = True
    Band_path = 'LGL'	    # Brillouin zone high symmetry points
    Band_npoints = 60		# Number of points between high symmetry points
    Energy_max = 5 		# eV. It is the maximum energy value for band structure and DOS figures.
    Energy_min = -5     # eV. It is the minimum energy value for band structure and DOS figures.
    Band_convergence = {'bands':8}   # Convergence items for band calculations

    # ELECTRON DENSITY ----------------------
    Refine_grid = 4             # refine grid for all electron density (1, 2 [=default] and 4)

    # PHONON -------------------------
    Phonon_PW_cutoff = 400
    Phonon_kpts_x = 3
    Phonon_kpts_y = 3
    Phonon_kpts_z = 3
    Phonon_supercell = np.diag([2, 2, 2])
    Phonon_displacement = 1e-3
    Phonon_path = 'LGL'	    # Brillouin zone high symmetry points
    Phonon_npoints = 60		# Number of points between high symmetry points
    Phonon_acoustic_sum_rule = True
    
    # GW CALCULATION ----------------------
    GW_calc_type = 'GW0'          # GW0 or G0W0
    GW_kpoints_list = np.array([[0.0, 0.0, 0.0], [1 / 3, 1 / 3, 0], [0.0, 0.0, 0.0]]) #Kpoints list
    GW_truncation = 'None'     # Can be None, '2D', '1D', '0D' or 'wigner-seitz'
    GW_cut_off_energy = 50   # Cut-off energy
    GW_valence_band_no = 8            # Valence band number
    GW_conudction_band_no = 18           # Conduction band number
    GW_PPA = True            # Plasmon Pole Approximation
    GW_q0_correction = True   # Analytic correction to the q=0 contribution applicable to 2D systems.
    GW_nblocks_max = True         # Cuts chi0 into as many blocks to reduce mem. req. as much as possible.
    GW_interpolate_band = True # Interpolate band

    # OPTICAL ----------------------
    Opt_calc_type = 'BSE'         # BSE or RPA
    Opt_shift_en = 0.0          # Shifting of the energy
    Opt_BSE_valence = range(0,3)  # Valence bands that will be used in BSE calculation
    Opt_BSE_conduction = range(4,7) # Conduction bands that will be used in BSE calculation
    Opt_BSE_min_en = 0.0       # Results will be started from this energy (BSE only)
    Opt_BSE_max_en = 20.0      # Results will be ended at this energy (BSE only)
    Opt_BSE_num_of_data = 1001   # Number of data points in BSE  calculation
    Opt_num_of_bands = 8	# Number of bands
    Opt_FD_smearing = 0.05       # Fermi Dirac smearing for optical calculations
    Opt_eta = 0.05             # Eta for Optical calculations
    Opt_domega0 = 0.05         # Domega0 for Optical calculations
    Opt_omega2 = 5.0           # Frequency at which the non-lin freq grid has doubled the spacing
    Opt_cut_of_energy = 100             # Cut-off energy for optical calculations
    Opt_nblocks = 4            # Split matrices in nblocks blocks and distribute them G-vectors
                            # or frequencies over processes. Also can use world.size

    #GENERAL ----------------------
    MPI_cores = 4            # This is for gg.py. Not used in this script.

    # -------------------------------------------------------------
    # Bulk Configuration
    # -------------------------------------------------------------
    bulk_configuration = Atoms(
        [
        Atom('C', ( 0.0, 0.0, 5.0 )),
        Atom('C', ( -1.2339999999999995, 2.1373506965399947, 5.0 )),
        Atom('C', ( 2.4679999999999995, 0.0, 5.0 )),
        Atom('C', ( 1.234, 2.1373506965399947, 5.0 )),
        Atom('C', ( 2.468000000230841e-06, 1.424899039459532, 5.0 )),
        Atom('C', ( -1.2339975319999992, 3.5622497359995267, 5.0 )),
        Atom('C', ( 2.4680024680000003, 1.424899039459532, 5.0 )),
        Atom('C', ( 1.234002468000001, 3.5622497359995267, 5.0 )),
        ],
        cell=[(4.936, 0.0, 0.0), (-2.467999999999999, 4.274701393079989, 0.0), (0.0, 0.0, 20.0)],
        pbc=True,
        )

    # -------------------------------------------------------------
    # ///////   YOU DO NOT NEED TO CHANGE ANYTHING BELOW    \\\\\\\
    # -------------------------------------------------------------

    # Version
    __version__ = "v23.2.1b1"

    parser = ArgumentParser(prog ='gpawtools.py', description=Description, formatter_class=RawFormatter)
    parser.add_argument("-i", "--input", dest = "inputfile", help="Use input file for calculation variables (also you can insert geometry)")
    parser.add_argument("-g", "--geometry",dest ="geometryfile", help="Use CIF file for geometry")
    parser.add_argument("-v", "--version", dest="version", action='store_true')
    parser.add_argument("-e", "--energy", dest="energymeas", action='store_true')
    parser.add_argument("-r", "--restart", dest="restart", action='store_true')
    parser.add_argument("-p", "--passground", dest="passground", action='store_true')
    parser.add_argument("-d", "--drawfigures", dest="drawfigs", action='store_true', help="Draws DOS and band structure figures at the end of calculation.")

    args = None

    # Parse arguments
    try:
        if world.rank == 0:
            args = parser.parse_args()
    finally:
        args = broadcast(args, root=0, comm=world)

    if args is None:
        parprint("No arguments used.")
        quit()

    # DEFAULT VALUES
    restart = False
    passground = False
    energymeas = False
    inFile = None
    drawfigs = False
    configpath = None
    Outdirname = ''
    
    try:
        if args.inputfile is not None:
            configpath = os.path.join(os.getcwd(),args.inputfile)
            sys.path.append(os.getcwd())


        if args.geometryfile :
            inFile = os.path.join(os.getcwd(),args.geometryfile)

        if args.drawfigs == True:
            drawfigs = True
            
        if args.energymeas == True:
            try:
                import pyRAPL
                energymeas = True
                # Start energy consumption calculation.
                pyRAPL.setup()
                meter = pyRAPL.Measurement('gpawsolve')
                meter.begin()
            except:
                parprint("\033[91mERROR:\033[0m Unexpected error while using -e argument.")
                parprint("-e works only with Intel CPUs after Sandy Bridge generation. Do not use with AMD CPUs")
                parprint("You also need to install pymongo and pandas libraries.")
                parprint("If you got permission error, try: sudo chmod -R a+r /sys/class/powercap/intel-rapl")
                parprint("More information about the error:")
                parprint(sys.exc_info()[0])
                quit()
        if args.version == True:
            import gpaw
            import ase
            import phonopy
            try:
                response = requests.get("https://api.github.com/repos/lrgresearch/gpaw-tools/releases/latest", timeout=5)
                parprint('---------------------------------------------------------------------------------------')
                parprint('\033[95mgpaw-tools:\033[0m Version information: '+str(__version__))
                parprint('  uses GPAW '+gpaw.__version__+', ASE '+ase.__version__+' and PHONOPY '+phonopy.__version__)
                parprint('---------------------------------------------------------------------------------------')
                parprint('The latest STABLE release was '+response.json()["tag_name"]+', which is published at '+response.json()["published_at"])
                parprint('Download the latest STABLE tarball release at: '+response.json()["tarball_url"])
                parprint('Download the latest STABLE zipball release at: '+response.json()["zipball_url"])
                parprint('Download the latest DEV zipball release at: https://github.com/lrgresearch/gpaw-tools/archive/refs/heads/main.zip')
            except (requests.ConnectionError, requests.Timeout) as exception:
                parprint('---------------------------------------------------------------------------------------')
                parprint('\033[95mgpaw-tools:\033[0m Version information: '+str(__version__))
                parprint('  uses GPAW '+gpaw.__version__+', ASE '+ase.__version__+' and PHONOPY '+phonopy.__version__)
                parprint('---------------------------------------------------------------------------------------')
                parprint('No internet connection available.')
            quit()
        if args.restart == True:
            parprint('ATTENTION: -r, --restart argument is depreceted. It was just passing the ground calculations not restarting anything.')
            parprint('New argument for passing the ground state calculations is -p or -passground.')
            quit()   
        
        if args.passground == True:
            passground = True

    except getopt.error as err:
        # output error, and return with an error code
        parprint (str(err))

    # Start time
    time0 = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
    
    # Load struct
    struct = struct_from_file(inputfile = configpath, geometryfile = inFile)

    # Write timings of calculation
    with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
        print("gpawsolve.py execution timings (seconds):", end="\n", file=f1)
        print("Execution started:", time0, end="\n", file=f1)
    
    # Load gpawsolve() class
    gpawsolver = gpawsolve(struct)
    
    # Run structure calculation
    gpawsolver.structurecalc()
    
    if Optical_calc == False:
        # Run ground state calculation
        gpawsolver.groundcalc()
        
        if Elastic_calc == True:
            # Run elastic calculation
            gpawsolver.elasticcalc(drawfigs = drawfigs)
            
        if DOS_calc == True:
            # Run DOS calculation
            gpawsolver.doscalc(drawfigs = drawfigs)
            
        if Band_calc == True:
            # Run band calculation
            gpawsolver.bandcalc(drawfigs = drawfigs)
            
        if Density_calc == True:
            # Run all-electron density calculation
            gpawsolver.densitycalc()    
            
        if Phonon_calc == True:
            # Run phonon calculation
            gpawsolver.phononcalc()  
    else:
        # Run optical calculation
        gpawsolver.opticalcalc()
    
    # Ending of timings
    with paropen(struct+'-7-Result-Log-Timings.txt', 'a') as f1:
        print("---------------------------------------", end="\n", file=f1)

    if args.energymeas == True:
        # Ending of energy consumption measuring.
        meter.end()
        energyresult=meter.result
        with paropen(struct+'-8-Result-Log-Energyconsumption.txt', 'a') as f1:
            print("Energy measurement:-----------------------------------------", end="\n", file=f1)
            print(1e-6*energyresult.duration," Computation time in seconds", end="\n", file=f1)
            print(1e-6*sum(energyresult.pkg)," CPU energy consumption in Joules", end="\n", file=f1)
            print(1e-6*sum(energyresult.dram)," DRAM energy consumption in Joules", end="\n", file=f1)
            print(2.77777778e-7*(1e-6*sum(energyresult.dram)+1e-6*sum(energyresult.pkg))," Total energy consumption in kWh", end="\n", file=f1)

