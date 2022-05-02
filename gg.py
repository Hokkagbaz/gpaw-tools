#!/usr/bin/env python

'''
gg.py: GUI for gpawsolve.py
Usage: $ gg.py
'''
import os, io, sys
from shlex import split
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, BooleanVar, StringVar
import pathlib
import subprocess
import shutil
from ase.visualize import view
from ase.io import read, write
import webbrowser

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
WORK_PATH = os.getcwd()
class gg:
    ''' Main class'''
    Struct = ""
    StructLoaded = False

    def __init__(self, master=None):
        global Elastic_calcvar, DOS_calcvar, Band_calcvar, Density_calcvar, Optical_calcvar, Spin_calcvar, GWppavar, GWq0correctionvar, GWnblockvar
        global EpsXvar, EpsYvar, EpsZvar, ShearYZvar, ShearXZvar, ShearXYvar, restartvar, Gammavar, Fix_symmetryvar
        global Struct, StructLoaded, GWbandinterpolationvar
        
        url = 'https://www.lrgresearch.org/gpaw-tools/'
        
        def OpenUrl(url):
            webbrowser.open_new(url)
    
        def onOpen():
            ''' This is the open button's behaviour on the first tab.'''
            global basename, basepath, textfilenamepath
            global Struct, StructLoaded
            textfile = filedialog.askopenfilename(initialdir = os.getcwd(), title = "Open file",
                                                  filetypes = (("CIF files","*.cif"),
                                                  ("All files","*.*")))
            textfilenamepath = textfile
            p = pathlib.PurePath(textfilenamepath)
            basename = StringVar()
            basename = pathlib.Path(textfilenamepath).stem
            basepath = StringVar()
            basepath = p.parents[0]
            #textfile.close()
            self.text1.insert(tk.END, "File opened: "+basename+" \n")
            # Opening a working directory
            #if not os.path.isdir(os.path.join(basepath,basename)):
                #os.makedirs(os.path.join(basepath,basename), exist_ok=True)
            asestruct = read(textfilenamepath, index='-1')
            Struct = asestruct
            StructLoaded = True
            write(os.path.join(p.parents[0], basename)+'_InitialStructure.png', asestruct)
            self.structureimage = tk.PhotoImage(file=os.path.join(p.parents[0], basename)+'_InitialStructure.png')
            self.button2.configure(image=self.structureimage, style='Toolbutton', text='button2')

            
        def onConfigOpen():
            ''' This is the Configuration file open button's behaviour on the first tab.'''
            global configname
            textfile = filedialog.askopenfilename(initialdir = WORK_PATH, title = "Open file",
                                                  filetypes = (("PY files","*.py"),
                                                  ("All files","*.*")))
            configname = textfile
            # Prepare a temporary config file for process
            shutil.copy2(textfile, os.path.join(WORK_PATH,pathlib.Path(configname).stem+'_temp.py')) 
            configname = os.path.join(WORK_PATH, pathlib.Path(configname).stem+'_temp.py')
            # Loading config file
            sys.path.append(WORK_PATH)
            config = __import__(pathlib.Path(configname).stem)

            
            # There must be some elegant way to do this.
            # Searching in globals() make us to use less parameters in config files. Otherwise not using a variable in
            # a congig file gives errors.
            
            # Mode
            self.text1.insert(tk.END, config.__dict__.keys())
            if 'Mode' in config.__dict__.keys():
                if config.Mode == 'PW':
                    self.Modettk.current(0)
                elif config.Mode == 'PW-GW':
                    self.Modettk.current(1)
                elif config.Mode == 'EXX':
                    self.Modettk.current(2)
                elif config.Mode == 'LCAO':
                    self.Modettk.current(3)
                elif config.Mode == 'FD':
                    self.Modettk.current(4)
                else:
                    self.Modettk.current(0)
            else:
                self.Modettk.current(2)

            # Elastic calculation    
            if 'Elastic_calc' in config.__dict__.keys():
                if config.Elastic_calc == True:
                    Elastic_calcvar.set(True)
                else:
                    Elastic_calcvar.set(False)
            else:
                Elastic_calcvar.set(False)
                
            # DOS calculation    
            if 'DOS_calc' in config.__dict__.keys():
                if config.DOS_calc == True:
                    DOS_calcvar.set(True)
                else:
                    DOS_calcvar.set(False)
            else:
                DOS_calcvar.set(False)

            # Band calculation
            if 'Band_calc' in config.__dict__.keys():
                if config.Band_calc == True:
                    Band_calcvar.set(True)
                else:
                    Band_calcvar.set(False)
            else:
                Band_calcvar.set(False)

            # Density calculation
            if 'Density_calc' in config.__dict__.keys():
                if config.Density_calc == True:
                    Density_calcvar.set(True)
                else:
                    Density_calcvar.set(False)
            else:
                Density_calcvar.set(False)

            # Optical calculation
            if 'Optical_calc' in config.__dict__.keys():
                if config.Optical_calc == True:
                    Optical_calcvar.set(True)
                else:
                    Optical_calcvar.set(False)
            else:
                Optical_calcvar.set(False)

            # Fmax
            if 'fmaxval' in config.__dict__.keys():
                self.fmaxvalttk.delete('0', 'end')
                self.fmaxvalttk.insert('0', config.fmaxval)
            else:
                self.fmaxvalttk.delete('0', 'end')
                self.fmaxvalttk.insert('0', '0.05')
            
            # Fix_symmetry    
            if 'Fix_symmetry' in config.__dict__.keys():
                if config.Fix_symmetry == True:
                    Fix_symmetryvar.set(True)
                else:
                    Fix_symmetryvar.set(False)
            else:
                Fix_symmetryvar.set(False)

            # Cut-off energy
            if 'cut_off_energy' in config.__dict__.keys():
                self.cut_off_energyttk.delete('0', 'end')
                self.cut_off_energyttk.insert('0', config.cut_off_energy)
            else:
                self.cut_off_energyttk.delete('0', 'end')
                self.cut_off_energyttk.insert('0', '340')

            # Kpoints
            if 'kpts_x' in config.__dict__.keys():
                self.kpts_xttk.delete('0', 'end')
                self.kpts_xttk.insert('0', config.kpts_x)
                self.kpts_yttk.delete('0', 'end')
                self.kpts_yttk.insert('0', config.kpts_y)
                self.kpts_zttk.delete('0', 'end')
                self.kpts_zttk.insert('0', config.kpts_z)
            else:
                self.kpts_xttk.delete('0', 'end')
                self.kpts_xttk.insert('0', '1')
                self.kpts_yttk.delete('0', 'end')
                self.kpts_yttk.insert('0', '1')
                self.kpts_zttk.delete('0', 'end')
                self.kpts_zttk.insert('0', '1')

            # Gamma
            if 'Gamma' in config.__dict__.keys():
                if config.Gamma == True:
                    Gammavar.set(True)
                else:
                    Gammavar.set(False)
            else:
                Gammavar.set(False)

            # Band path
            if 'band_path' in config.__dict__.keys():
                self.band_pathttk.delete('0', 'end')
                self.band_pathttk.insert('0', config.band_path)
            else:
                self.band_pathttk.delete('0', 'end')
                self.band_pathttk.insert('0', 'GX')

            # Npoints
            if 'band_npoints' in config.__dict__.keys():
                self.band_npointsttk.delete('0', 'end')
                self.band_npointsttk.insert('0', config.band_npoints)
            else:
                self.band_npointsttk.delete('0', 'end')
                self.band_npointsttk.insert('0', '40')

            # Max energy for figure
            if 'energy_max' in config.__dict__.keys():
                self.energy_maxttk.delete('0', 'end')
                self.energy_maxttk.insert('0', config.energy_max)
            else:
                self.energy_maxttk.delete('0', 'end')
                self.energy_maxttk.insert('0', '15')

            
            # Hubbard
            if 'Hubbard' in config.__dict__.keys():
                self.Hubbardttk.delete('0', 'end')
                if hasattr(config, 'Hubbard'):
                    self.Hubbardttk.insert('0', str(config.Hubbard))
                else:
                    self.Hubbardttk.insert('0', '{}')
            else:
                self.Hubbardttk.delete('0', 'end')
                self.Hubbardttk.insert('0', '{}')

            # XCs
            if 'XC_calc' in config.__dict__.keys():
                if config.XC_calc == 'LDA':
                    self.XC_calcttk.current(0)
                elif config.XC_calc == 'PBE':
                    self.XC_calcttk.current(1)
                elif config.XC_calc == 'GLLBSC':
                    self.XC_calcttk.current(2)
                elif config.XC_calc == 'revPBE':
                    self.XC_calcttk.current(3)
                elif config.XC_calc == 'RPBE':
                    self.XC_calcttk.current(4)
                elif config.XC_calc == 'PBE0':
                    self.XC_calcttk.current(5)
                elif config.XC_calc == 'HSE06':
                    self.XC_calcttk.current(6)
                else:
                    self.XC_calcttk.current(0)
            else:
                self.XC_calcttk.current(0)

            # Ground_convergence
            if 'Ground_convergence' in config.__dict__.keys():
                self.Ground_convergencettk.delete('0', 'end')
                if hasattr(config, 'Ground_convergence'):
                    self.Ground_convergencettk.insert('0', str(config.Ground_convergence))
                else:
                    self.Ground_convergencettk.insert('0', '{}')
            else:
                self.Ground_convergencettk.delete('0', 'end')
                self.Ground_convergencettk.insert('0', '{}')

            # Band_convergence
            if 'Band_convergence' in config.__dict__.keys():
                self.Band_convergencettk.delete('0', 'end')
                if hasattr(config, 'Band_convergence'):
                    self.Band_convergencettk.insert('0', str(config.Band_convergence))
                else:
                    self.Band_convergencettk.insert('0', "{'bands':8}")
            else:
                self.Band_convergencettk.delete('0', 'end')
                self.Band_convergencettk.insert('0', "{'bands':8}")

            # Occupation
            if 'Occupation' in config.__dict__.keys():
                self.Occupationttk.delete('0', 'end')
                if hasattr(config, 'Occupation'):
                    self.Occupationttk.insert('0', str(config.Occupation))
                else:
                    self.Occupationttk.insert('0', "{'name': 'fermi-dirac', 'width': 0.05}")
            else:
                self.Occupationttk.delete('0', 'end')
                self.Occupationttk.insert('0', "{'name': 'fermi-dirac', 'width': 0.05}")

            # DOS number of points
            if 'DOS_npoints' in config.__dict__.keys():
                self.energy_maxttk.delete('0', 'end')
                self.energy_maxttk.insert('0', config.DOS_npoints)
            else:
                self.energy_maxttk.delete('0', 'end')
                self.energy_maxttk.insert('0', '501')

            # DOS smearing width
            if 'DOS_width' in config.__dict__.keys():
                self.energy_maxttk.delete('0', 'end')
                self.energy_maxttk.insert('0', config.DOS_width)
            else:
                self.energy_maxttk.delete('0', 'end')
                self.energy_maxttk.insert('0', '0.1')

            # Spin Calculation
            if 'Spin_calc' in config.__dict__.keys():
                if config.Spin_calc == True:
                    Spin_calcvar.set(True)
                else:
                    Spin_calcvar.set(False)
            else:
                Spin_calcvar.set(False)

            # Magnetic Moment
            if 'Magmom_per_atom' in config.__dict__.keys():
                self.Magmom_per_atomttk.delete('0', 'end')
                self.Magmom_per_atomttk.insert('0', config.Magmom_per_atom)
            else:
                self.Magmom_per_atomttk.delete('0', 'end')
                self.Magmom_per_atomttk.insert('0', '0.0')

            #Gridref for electron density
            if 'gridref' in config.__dict__.keys():
                self.gridrefttk.delete('0', 'end')
                self.gridrefttk.insert('0', config.gridref)
            else:
                self.gridrefttk.delete('0', 'end')
                self.gridrefttk.insert('0', '2')        

            # ---------GW Parameters---------
            
            # GWtype
            if 'gridref' in config.__dict__.keys():
                if config.GWtype == 'GW0':
                    self.GWtypettk.current(0)
                elif config.GWtype == 'G0W0':
                    self.GWtypettk.current(1)
                else:
                    self.GWtypettk.current(0)
            else:
                self.GWtypettk.current(0)
            
            # GWkpoints
            if 'GWkpoints' in config.__dict__.keys():
                self.GWkpointsttk.delete('0', 'end')
                if hasattr(config, 'GWkpoints'):
                    self.GWkpointsttk.insert('0', str(config.GWkpoints.tolist()))
                else:
                    self.GWkpointsttk.insert('0', '[[0.0, 0.0, 0.0], [1 / 3, 1 / 3, 0], [0.0, 0.0, 0.0]]')
            else:
                self.GWkpointsttk.delete('0', 'end')
                self.GWkpointsttk.insert('0', '[[0.0, 0.0, 0.0], [1 / 3, 1 / 3, 0], [0.0, 0.0, 0.0]]')
            
            # GWtruncation
            if 'GWtruncation' in config.__dict__.keys():
                if config.GWtruncation is None:
                    self.GWtruncationttk.current(0)
                elif config.GWtruncation == '2D':
                    self.GWtruncationttk.current(1)
                elif config.GWtruncation == '1D':
                    self.GWtruncationttk.current(2)
                elif config.GWtruncation == '0D':
                    self.GWtruncationttk.current(3)
                elif config.GWtruncation == 'wigner-seitz':
                    self.GWtruncationttk.current(4)
                else:
                    self.GWtruncationttk.current(0)
            else:
                self.GWtruncationttk.current(0)

            # GWcut_off_energy
            if 'GWcut_off_energy' in config.__dict__.keys():
                self.GWcut_off_energyttk.delete('0', 'end')
                self.GWcut_off_energyttk.insert('0', config.GWcut_off_energy)
            else:
                self.GWcut_off_energyttk.delete('0', 'end')
                self.GWcut_off_energyttk.insert('0', '50')

            # GWbandVB
            if 'GWbandVB' in config.__dict__.keys():
                self.GWbandVBttk.delete('0', 'end')
                self.GWbandVBttk.insert('0', config.GWbandVB)
            else:
                self.GWbandVBttk.delete('0', 'end')
                self.GWbandVBttk.insert('0', '8')

            # GWbandCB
            if 'GWbandCB' in config.__dict__.keys():
                self.GWbandCBttk.delete('0', 'end')
                self.GWbandCBttk.insert('0', config.GWbandCB)
            else:
                self.GWbandCBttk.delete('0', 'end')
                self.GWbandCBttk.insert('0', '18')

            # GWppa
            if 'GWppa' in config.__dict__.keys():
                if config.GWppa == True:
                    GWppavar.set(True)
                else:
                    GWppavar.set(False)
            else:
                GWppavar.set(False)
                
            # GWq0correction
            if 'GWq0correction' in config.__dict__.keys():
                if config.GWq0correction == True:
                    GWq0correctionvar.set(True)
                else:
                    GWq0correctionvar.set(False)
            else:
                GWq0correctionvar.set(False)

            # GWnblock
            if 'GWnblock' in config.__dict__.keys():
                if config.GWnblock == True:
                    GWnblockvar.set(True)
                else:
                    GWnblockvar.set(False)
            else:
                GWnblockvar.set(False)

            # GWbandinterpolation
            if 'GWbandinterpolation' in config.__dict__.keys():
                if config.GWbandinterpolation == True:
                    GWbandinterpolationvar.set(True)
                else:
                    GWbandinterpolationvar.set(False)
            else:
                GWbandinterpolationvar.set(True)

            # ---------Optical------------

            # Type
            if 'opttype' in config.__dict__.keys():
                if config.opttype == 'BSE':
                    self.opttypettk.current(0)
                elif config.opttype == 'RPA':
                    self.opttypettk.current(1)
                else:
                    self.opttypettk.current(0)
            else:
                self.opttypettk.current(0)
            
            # Shifting
            if 'optshift' in config.__dict__.keys():
                self.optshiftttk.delete('0', 'end')
                self.optshiftttk.insert('0', config.optshift)
            else:
                self.optshiftttk.delete('0', 'end')
                self.optshiftttk.insert('0', '0.0')
            
            # Valance bands for BSE calculation
            if 'optBSEvb' in config.__dict__.keys():
                self.optBSEvbttk.delete('0', 'end')
                if hasattr(config, 'optBSEvb'):
                    self.optBSEvbttk.insert('0', str(config.optBSEvb))
                else:
                    self.optBSEvbttk.insert('0', 'range(0,4)')
            else:
                self.optBSEvbttk.delete('0', 'end')
                self.optBSEvbttk.insert('0', 'range(0,4)')
            
            # Conduction bands for BSE calculation
            if 'optBSEcb' in config.__dict__.keys():
                self.optBSEcbttk.delete('0', 'end')
                if hasattr(config, 'optBSEcb'):
                    self.optBSEcbttk.insert('0', str(config.optBSEcb))
                else:
                    self.optBSEcbttk.insert('0', 'range(4,7)')
            else:
                self.optBSEcbttk.delete('0', 'end')
                self.optBSEcbttk.insert('0', 'range(4,7)')
            
            # Minimum energy value for BSE calculation
            if 'optBSEminEn' in config.__dict__.keys():
                self.optBSEminEnttk.delete('0', 'end')
                self.optBSEminEnttk.insert('0', config.optBSEminEn)
            else:
                self.optBSEminEnttk.delete('0', 'end')
                self.optBSEminEnttk.insert('0', '0.0')
            
            # Maximum energy value for BSE calculation
            if 'optBSEmaxEn' in config.__dict__.keys():
                self.optBSEmaxEnttk.delete('0', 'end')
                self.optBSEmaxEnttk.insert('0', config.optBSEmaxEn)
            else:
                self.optBSEmaxEnttk.delete('0', 'end')
                self.optBSEmaxEnttk.insert('0', '20.0')
            
            # Number of data for BSE calculation
            if 'optBSEnumdata' in config.__dict__.keys():
                self.optBSEnumdatattk.delete('0', 'end')
                self.optBSEnumdatattk.insert('0', config.optBSEnumdata)
            else:
                self.optBSEnumdatattk.delete('0', 'end')
                self.optBSEnumdatattk.insert('0', '1001')
            
            # Number of bands
            if 'num_of_bands' in config.__dict__.keys():
                self.num_of_bandsttk.delete('0', 'end')
                self.num_of_bandsttk.insert('0', config.num_of_bands)
            else:
                self.num_of_bandsttk.delete('0', 'end')
                self.num_of_bandsttk.insert('0', '16')

            # Fermi-Dirac Smearing
            if 'optFDsmear' in config.__dict__.keys():
                self.optFDsmearttk.delete('0', 'end')
                self.optFDsmearttk.insert('0', config.optFDsmear)
            else:
                self.optFDsmearttk.delete('0', 'end')
                self.optFDsmearttk.insert('0', '0.05')

            # Eta
            if 'opteta' in config.__dict__.keys():
                self.optetattk.delete('0', 'end')
                self.optetattk.insert('0', config.opteta)
            else:
                self.optetattk.delete('0', 'end')
                self.optetattk.insert('0', '0.05')

            # DOmega0
            if 'optdomega0' in config.__dict__.keys():
                self.optdomega0ttk.delete('0', 'end')
                self.optdomega0ttk.insert('0', config.optdomega0)
            else:
                self.optdomega0ttk.delete('0', 'end')
                self.optdomega0ttk.insert('0', '0.05')

            # Optical nblocks
            if 'optnblocks' in config.__dict__.keys():
                self.optnblocksttk.delete('0', 'end')
                self.optnblocksttk.insert('0', config.optnblocks)
            else:
                self.optnblocksttk.delete('0', 'end')
                self.optnblocksttk.insert('0', '4')
            
            # Omega2
            if 'optomega2' in config.__dict__.keys():
                self.optomega2ttk.delete('0', 'end')
                self.optomega2ttk.insert('0', config.optomega2)
            else:
                self.optomega2ttk.delete('0', 'end')
                self.optomega2ttk.insert('0', '5.0')

            # Optical cut off
            if 'optecut' in config.__dict__.keys():
                self.optecutttk.delete('0', 'end')
                self.optecutttk.insert('0', config.optecut)
            else:
                self.optecutttk.delete('0', 'end')
                self.optecutttk.insert('0', '100')

            # Strain-Shear
            if 'whichstrain' in config.__dict__.keys():
                if config.whichstrain[0] == True:
                    EpsXvar.set(True)
                else:
                    EpsXvar.set(False)

                if config.whichstrain[1] == True:
                    EpsYvar.set(True)
                else:
                    EpsYvar.set(False)

                if config.whichstrain[2] == True:
                    EpsZvar.set(True)
                else:
                    EpsZvar.set(False)

                if config.whichstrain[3] == True:
                    ShearYZvar.set(True)
                else:
                    ShearYZvar.set(False)

                if config.whichstrain[4] == True:
                    ShearXZvar.set(True)
                else:
                    ShearXZvar.set(False)

                if config.whichstrain[5] == True:
                    ShearXYvar.set(True)
                else:
                    ShearXYvar.set(False)
            else:
                EpsXvar.set(False)
                EpsYvar.set(False)
                EpsZvar.set(False)
                ShearYZvar.set(False)
                ShearXZvar.set(False)
                ShearXYvar.set(False)

            #Core number
            if 'MPIcores' in config.__dict__.keys():
                self.MPIcoresttk.delete('0', 'end')
                self.MPIcoresttk.insert('0', config.MPIcores)
            else:
                self.MPIcoresttk.delete('0', 'end')
                self.MPIcoresttk.insert('0', '1')
            
            # Text for textbox
            self.text1.insert(tk.END, "Configuration loaded, please continue with Input parameters tab \n")

        def onCalculate():
            '''Calculate button's behaviour'''
            #Firstly, lets save all options to config file.
            with open(configname, 'w') as f1:
                print("import numpy as np", end="\n", file=f1)

                # ---------Ground------------
                if self.Modettk.get() == 'PW':
                    print("Mode = 'PW'", end="\n", file=f1)
                elif self.Modettk.get() == 'PW-GW':
                    print("Mode = 'PW-GW'", end="\n", file=f1)
                elif self.Modettk.get() == 'EXX':
                    print("Mode = 'EXX'", end="\n", file=f1)
                elif self.Modettk.get() == 'LCAO':
                    print("Mode = 'LCAO'", end="\n", file=f1)
                elif self.Modettk.get() == 'FD':
                    print("Mode = 'FD'", end="\n", file=f1)
                else:
                    print("Mode = 'PW'", end="\n", file=f1)
                # Elastic_calc
                print("Elastic_calc = "+ str(Elastic_calcvar.get()), end="\n", file=f1)
                # DOS_calc
                print("DOS_calc = "+ str(DOS_calcvar.get()), end="\n", file=f1)
                # Band_calc
                print("Band_calc = "+ str(Band_calcvar.get()), end="\n", file=f1)
                # Density_calc
                print("Density_calc = "+ str(Density_calcvar.get()), end="\n", file=f1)
                # Optical_calc
                print("Optical_calc = "+ str(Optical_calcvar.get()), end="\n", file=f1)
                # ---------Electronic------------
                # fmaxval
                print("fmaxval = "+ str(self.fmaxvalttk.get()), end="\n", file=f1)
                #Fix_symmetry
                print("Fix_symmetry = "+ str(Fix_symmetryvar.get()), end="\n", file=f1)
                # cut_off_energy
                print("cut_off_energy = "+ str(self.cut_off_energyttk.get()), end="\n", file=f1)
                # kpoints
                print("kpts_x = "+ str(self.kpts_xttk.get()), end="\n", file=f1)
                print("kpts_y = "+ str(self.kpts_yttk.get()), end="\n", file=f1)
                print("kpts_z = "+ str(self.kpts_zttk.get()), end="\n", file=f1)
                # Gamma
                print("Gamma = "+ str(Gammavar.get()), end="\n", file=f1)
                # band_path
                print("band_path = '"+ str(self.band_pathttk.get())+"'", end="\n", file=f1)
                # band_npoints
                print("band_npoints = "+ str(self.band_npointsttk.get()), end="\n", file=f1)
                # energy_max
                print("energy_max = "+ str(self.energy_maxttk.get()), end="\n", file=f1)
                # Hubbard
                print("Hubbard = "+ str(self.Hubbardttk.get()), end="\n", file=f1)
                # Exchange-Correlation
                if self.XC_calcttk.get() == 'LDA':
                    print("XC_calc = 'LDA'", end="\n", file=f1)
                elif self.XC_calcttk.get() == 'PBE':
                    print("XC_calc = 'PBE'", end="\n", file=f1)
                elif self.XC_calcttk.get() == 'GLLBSC':
                    print("XC_calc = 'GLLBSC'", end="\n", file=f1)
                elif self.XC_calcttk.get() == 'revPBE':
                    print("XC_calc = 'revPBE'", end="\n", file=f1)
                elif self.XC_calcttk.get() == 'RPBE':
                    print("XC_calc = 'RPBE'", end="\n", file=f1)
                elif self.XC_calcttk.get() == 'PBE0':
                    print("XC_calc = 'PBE0'", end="\n", file=f1)
                elif self.XC_calcttk.get() == 'HSE06':
                    print("XC_calc = 'HSE06'", end="\n", file=f1)
                else:
                    print("XC_calc = 'LDA'", end="\n", file=f1)
                # Ground_convergence
                print("Ground_convergence = "+ str(self.Ground_convergencettk.get()), end="\n", file=f1)
                # Band_convergence
                print("Band_convergence = "+ str(self.Band_convergencettk.get()), end="\n", file=f1)
                # Occupation
                print("Occupation = "+ str(self.Occupationttk.get()), end="\n", file=f1)
                # DOS_npoints
                print("DOS_npoints = "+ str(self.DOS_npointsttk.get()), end="\n", file=f1)
                # DOS_width
                print("DOS_width = "+ str(self.DOS_widthttk.get()), end="\n", file=f1)
                # Spin_calc
                print("Spin_calc = "+ str(Spin_calcvar.get()), end="\n", file=f1)
                # Magmom_per_atom
                print("Magmom_per_atom = "+ str(self.Magmom_per_atomttk.get()), end="\n", file=f1)
                # gridref
                print("gridref = "+ str(self.gridrefttk.get()), end="\n", file=f1)
                
                # ---------GW Parameters------------
                # GWtype
                if self.GWtypettk.get() == 'GW0':
                    print("GWtype = 'GW0'", end="\n", file=f1)
                elif self.GWtypettk.get() == 'G0W0':
                    print("GWtype = 'G0W0'", end="\n", file=f1)
                else:
                    print("GWtype = 'GW0'", end="\n", file=f1)
                # GWtruncation
                if self.GWtruncationttk.get() == '':
                    print("GWtruncation = None", end="\n", file=f1)
                elif self.GWtruncationttk.get() == '2D':
                    print("GWtruncation = '2D'", end="\n", file=f1)
                elif self.GWtruncationttk.get() == '1D':
                    print("GWtruncation = '1D'", end="\n", file=f1)
                elif self.GWtruncationttk.get() == '0D':
                    print("GWtruncation = '0D'", end="\n", file=f1)
                else:
                    print("GWtruncation = 'wigner-seitz'", end="\n", file=f1)               
                # GWkpoints
                print("GWkpoints = np.array("+ str(self.GWkpointsttk.get())+")", end="\n", file=f1)
                # GWcut_off_energy
                print("GWcut_off_energy = "+ str(self.GWcut_off_energyttk.get()), end="\n", file=f1)
                # GWbandVB
                print("GWbandVB = "+ str(self.GWbandVBttk.get()), end="\n", file=f1)
                # GWbandCB
                print("GWbandCB = "+ str(self.GWbandCBttk.get()), end="\n", file=f1)
                # GWppa
                print("GWppa = "+ str(GWppavar.get()), end="\n", file=f1)
                # GWq0correction
                print("GWq0correction = "+ str(GWq0correctionvar.get()), end="\n", file=f1)
                # GWnblock
                print("GWnblock = "+ str(GWnblockvar.get()), end="\n", file=f1)
                # GWbandinterpolation
                print("GWbandinterpolation = "+ str(GWbandinterpolationvar.get()), end="\n", file=f1)

                # ---------Optical------------
                # opttype
                if self.opttypettk.get() == 'BSE':
                    print("opttype = 'BSE'", end="\n", file=f1)
                elif self.opttypettk.get() == 'RPA':
                    print("opttype = 'RPA'", end="\n", file=f1)
                else:
                    print("opttype = 'BSE'", end="\n", file=f1)
                # optshift
                print("optshift = "+ str(self.optshiftttk.get()), end="\n", file=f1)
                # optBSEvb
                print("optBSEvb = "+ str(self.optBSEvbttk.get()), end="\n", file=f1)
                # optBSEcb
                print("optBSEcb = "+ str(self.optBSEcbttk.get()), end="\n", file=f1)
                # optBSEminEn
                print("optBSEminEn = "+ str(self.optBSEminEnttk.get()), end="\n", file=f1)
                # optBSEmaxEn
                print("optBSEmaxEn = "+ str(self.optBSEmaxEnttk.get()), end="\n", file=f1)
                # optBSEnumdata
                print("optBSEnumdata = "+ str(self.optBSEnumdatattk.get()), end="\n", file=f1)
                # num_of_bands
                print("num_of_bands = "+ str(self.num_of_bandsttk.get()), end="\n", file=f1)
                # optFDsmear
                print("optFDsmear = "+ str(self.optFDsmearttk.get()), end="\n", file=f1)
                # opteta
                print("opteta = "+ str(self.optetattk.get()), end="\n", file=f1)
                # optdomega0
                print("optdomega0 = "+ str(self.optdomega0ttk.get()), end="\n", file=f1)
                # optnblocks
                print("optnblocks = "+ str(self.optnblocksttk.get()), end="\n", file=f1)
                # optomega2
                print("optomega2 = "+ str(self.optomega2ttk.get()), end="\n", file=f1)
                # optecut
                print("optecut = "+ str(self.optecutttk.get()), end="\n", file=f1)
                
                # ------------Other------------
                # whichstrain
                print("whichstrain = ["+str(EpsXvar.get())+", "+str(EpsYvar.get())+", "+str(EpsZvar.get())+", "+str(ShearYZvar.get())+", "+str(ShearXZvar.get())+", "+str(ShearXYvar.get())+"]", end="\n", file=f1)

                # This feature is not used by gpawsolve.py, this is only usable for gg.py
                print("MPIcores = "+ str(self.MPIcoresttk.get()), end="\n", file=f1)

            # Running the gpawsolve.py. Firstly, let's define a command, then proceed it.
            if restartvar == True:
                gpawcommand = 'mpirun -np '+str(self.MPIcoresttk.get())+' gpawsolve.py -o -r -d -i '+str(configname)+' -g '+str(textfilenamepath)
            else:
                gpawcommand = 'mpirun -np '+str(self.MPIcoresttk.get())+' gpawsolve.py -o -d -i '+str(configname)+' -g '+str(textfilenamepath)
            proc = subprocess.Popen(split(gpawcommand), shell=False, stdout = subprocess.PIPE)
            self.text1.insert(tk.END, "Command executed: "+gpawcommand+" \n")

            # Save stdout as a log
            #sys.path.append(os.path.abspath(configname))
            #config = __import__(pathlib.Path(configname).stem)
            
            #Looking for working directory
            if not os.path.isdir(os.path.join(os.path.dirname(configname), basename)):
                os.makedirs(os.path.join(os.path.dirname(configname), basename), exist_ok=True)
            
            with open(os.path.join(os.path.join(os.path.dirname(configname), basename), basename)+"-STDOUT-Log.txt", 'w') as f2:
                for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):  # or another encoding
                    self.text4.insert(tk.END, line)
                    print(line, end="\n", file=f2)
                self.text1.insert(tk.END, "Calculation finished... \n")
            self.text1.insert(tk.END, "STDOUT is also saved as log file. \n")

            # Read final cif file and save it as png:
            # /home/sblisesivdin/gpaw-tools-main/Cr2O_mp-1206821_primitive/Cr2O_mp-1206821_primitive-STDOUT-Log.txt
            asestruct = read(os.path.join(os.path.join(os.path.dirname(configname), basename), basename)+"-Final.cif", index='-1')
            write(os.path.join(os.path.join(os.path.dirname(configname), basename), basename)+'_FinalStructure.png', asestruct),
            
            shutil.move(os.path.join(basepath, basename)+'_InitialStructure.png', os.path.join(os.path.join(os.path.dirname(configname), basename), basename+'_InitialStructure.png'))
            os.remove(configname)
            self.text1.insert(tk.END, "Initial and Final Structure PNG files are saved to "+os.path.dirname(configname)+"/"+basename+" folder \n")

        def onASEload():
            '''When the user click on the structure image'''
            global Struct, StructLoaded
            if StructLoaded == True:
                # Open ASE GUI
                view(Struct)
        
        # build gui
        self.toplevel1 = tk.Tk() if master is None else tk.Toplevel(master)

        # --------- Load Structure tab -----------------
        self.frame2 = ttk.Frame(self.toplevel1)
        self.notebookUpper = ttk.Notebook(self.frame2)
        self.frame1 = ttk.Frame(self.notebookUpper)
        self.loadCIFfilettk = ttk.Button(self.frame1)
        self.loadCIFfilettk.configure(state='normal', text='Load Input (CIF, XSF, XSD, XYZ, etc.) File')
        self.loadCIFfilettk.pack(pady='10', side='top')
        self.loadCIFfilettk.configure(command=onOpen)
        
        self.loadConfigfilettk = ttk.Button(self.frame1)
        self.loadConfigfilettk.configure(state='normal', text='Load Configuration File')
        self.loadConfigfilettk.pack(pady='10', side='top')
        self.loadConfigfilettk.configure(command=onConfigOpen)

        self.button2 = ttk.Button(self.frame1)
        self.structureimage = tk.PhotoImage(file=os.path.join(PROJECT_PATH,'gui_files/gpaw-tools.png'))
        self.button2.configure(image=self.structureimage, style='Toolbutton', text='button2')
        self.button2.pack(side='top')
        self.button2.configure(command=onASEload)
        self.frame1.configure(height='200', width='200')
        self.frame1.pack(side='top')


        self.notebookUpper.add(self.frame1, text='Load Structure')
        
        # ----------- Input Parameters tab ----------------
        self.frame4 = ttk.Frame(self.notebookUpper)
        self.frame5 = ttk.Frame(self.frame4)
        
        # Labelframe1: Calculator Settings -------------------------------
        self.labelframe1 = ttk.Labelframe(self.frame5)

        # Label
        self.frame6 = ttk.Frame(self.labelframe1)
        self.label1 = ttk.Label(self.frame6)
        self.label1.configure(text='Calculator')
        self.label1.pack(side='left')

        # Mode
        self.Modettk = ttk.Combobox(self.frame6)
        self.Modettk.configure(values=('PW', 'PW-GW', 'EXX', 'LCAO', 'FD'), state='readonly')
        self.Modettk.pack(side='top')
        self.Modettk.current(0)
        self.frame6.configure(height='200', width='200')
        self.frame6.pack(side='top')
        
        # Elastic_calc
        self.Elastic_calcttk = ttk.Checkbutton(self.labelframe1)
        Elastic_calcvar = BooleanVar()
        self.Elastic_calcttk.configure(state='normal', variable = Elastic_calcvar, onvalue=True, offvalue=False, takefocus=False, text='Elastic Calculation')
        self.Elastic_calcttk.pack(side='top')
        
        # DOS_calc
        self.DOS_calcttk = ttk.Checkbutton(self.labelframe1)
        DOS_calcvar = BooleanVar()
        self.DOS_calcttk.configure(state='normal', variable = DOS_calcvar, onvalue=True, offvalue=False, takefocus=False, text='DOS Calculation')
        self.DOS_calcttk.pack(side='top')
        
        # Band_calc
        self.Band_calcttk = ttk.Checkbutton(self.labelframe1)
        Band_calcvar = BooleanVar()
        self.Band_calcttk.configure(variable = Band_calcvar, onvalue=True, offvalue=False, text='Band Structure Calculation')
        self.Band_calcttk.pack(side='top')
        
        # Density_calc
        self.Density_calcttk = ttk.Checkbutton(self.labelframe1)
        Density_calcvar = BooleanVar()
        self.Density_calcttk.configure(variable = Density_calcvar, onvalue=True, offvalue=False,text='All-Electron Density Calculation')
        self.Density_calcttk.pack(side='top')
        
        # Optical_calc
        self.Optical_calcttk = ttk.Checkbutton(self.labelframe1)
        Optical_calcvar = BooleanVar()
        self.Optical_calcttk.configure(variable = Optical_calcvar, onvalue=True, offvalue=False, text='Optical Properties Calculation')
        self.Optical_calcttk.pack(side='top')
        self.labelframe1.configure(height='200', text='Calculator Settings', width='200')
        self.labelframe1.pack(side='left')
        # End Labelframe1 ---------------------------------------------------
        
        # Labelframe2: Electronic Calculation Parameters --------------------
        self.labelframe2 = ttk.Labelframe(self.frame5)
 
        # Maximum Force
        self.frame7 = ttk.Frame(self.labelframe2)
        self.label5 = ttk.Label(self.frame7)
        self.label5.configure(text='Maximum Force')
        self.label5.pack(side='left')
        self.fmaxvalttk = ttk.Entry(self.frame7)
        self.fmaxvalttk.delete('0', 'end')
        self.fmaxvalttk.insert('0', '0.05')
        self.fmaxvalttk.pack(side='top')
        self.frame7.configure(height='200', width='200')
        self.frame7.pack(side='top')
        
        # Fix symmetry during optimization?
        self.frameFix_symmetry = ttk.Frame(self.labelframe2)
        self.Fix_symmetryttk = ttk.Checkbutton(self.frameFix_symmetry)
        Fix_symmetryvar = BooleanVar()
        self.Fix_symmetryttk.configure(variable = Fix_symmetryvar, onvalue=True, offvalue=False, text='Fix Symmetry')
        self.Fix_symmetryttk.pack(side='top')
        self.frameFix_symmetry.configure(height='200', width='200')
        self.frameFix_symmetry.pack(side='top')

        # Cut-off energy
        self.frame8 = ttk.Frame(self.labelframe2)
        self.label6 = ttk.Label(self.frame8)
        self.label6.configure(text='Cut-off energy (eV)')
        self.label6.pack(side='left')
        self.cut_off_energyttk = ttk.Entry(self.frame8)
        self.cut_off_energyttk.delete('0', 'end')
        self.cut_off_energyttk.insert('0', '340')
        self.cut_off_energyttk.pack(side='top')
        self.frame8.configure(height='200', width='200')
        self.frame8.pack(side='top')

        # K-points
        self.frame9 = ttk.Frame(self.labelframe2)
        self.label7 = ttk.Label(self.frame9)
        self.label7.configure(text='K-points (x,y,z)')
        self.label7.pack(side='left')
        self.kpts_xttk = ttk.Entry(self.frame9)
        self.kpts_xttk.configure(width='4')
        self.kpts_xttk.delete('0', 'end')
        self.kpts_xttk.insert('0', '1')
        self.kpts_xttk.pack(side='left')
        self.kpts_yttk = ttk.Entry(self.frame9)
        self.kpts_yttk.configure(width='4')
        self.kpts_yttk.delete('0', 'end')
        self.kpts_yttk.insert('0', '1')
        self.kpts_yttk.pack(side='left')
        self.kpts_zttk = ttk.Entry(self.frame9)
        self.kpts_zttk.configure(width='4')
        self.kpts_zttk.delete('0', 'end')
        self.kpts_zttk.insert('0', '1')
        self.kpts_zttk.pack(side='top')
        self.frame9.configure(height='200', width='200')
        self.frame9.pack(side='top')
        
        # Gamma
        self.frame23 = ttk.Frame(self.labelframe2)
        self.Gammattk = ttk.Checkbutton(self.frame23)
        Gammavar = BooleanVar()
        self.Gammattk.configure(variable = Gammavar, onvalue=True, offvalue=False, text='Gamma Included?')
        self.Gammattk.pack(side='top')
        self.frame23.configure(height='200', width='200')
        self.frame23.pack(side='top')
        
        # Band path
        self.frame10 = ttk.Frame(self.labelframe2)
        self.label8 = ttk.Label(self.frame10)
        self.label8.configure(text='Band Path (G:for Gamma)')
        self.label8.pack(side='left')
        self.band_pathttk = ttk.Entry(self.frame10)
        self.band_pathttk.delete('0', 'end')
        self.band_pathttk.insert('0', 'G')
        self.band_pathttk.pack(side='top')
        self.frame10.configure(height='200', width='200')
        self.frame10.pack(side='top')

        # Number of points
        self.frame11 = ttk.Frame(self.labelframe2)
        self.label9 = ttk.Label(self.frame11)
        self.label9.configure(text='# of points between symmetry points')
        self.label9.pack(side='left')
        self.band_npointsttk = ttk.Entry(self.frame11)
        self.band_npointsttk.delete('0', 'end')
        self.band_npointsttk.insert('0', '40')
        self.band_npointsttk.pack(side='top')
        self.frame11.configure(height='200', width='200')
        self.frame11.pack(side='top')

        # Maximum Energy
        self.frame12 = ttk.Frame(self.labelframe2)
        self.label10 = ttk.Label(self.frame12)
        self.label10.configure(text='Maximum energy')
        self.label10.pack(side='left')
        self.energy_maxttk = ttk.Entry(self.frame12)
        self.energy_maxttk.delete('0', 'end')
        self.energy_maxttk.insert('0', '10')
        self.energy_maxttk.pack(side='top')
        self.frame12.configure(height='200', width='200')
        self.frame12.pack(side='top')

        # Hubbard
        self.frameHubbard = ttk.Frame(self.labelframe2)
        self.labelHubbard = ttk.Label(self.frameHubbard)
        self.labelHubbard.configure(text='Hubbard Params.({} for none):')
        self.labelHubbard.pack(side='left')
        self.Hubbardttk = ttk.Entry(self.frameHubbard)
        self.Hubbardttk.delete('0', 'end')
        self.Hubbardttk.insert('0', '{}')
        self.Hubbardttk.pack(side='top')
        self.frameHubbard.configure(height='200', width='200')
        self.frameHubbard.pack(side='top')

        # XC
        self.frame14 = ttk.Frame(self.labelframe2)
        self.label11 = ttk.Label(self.frame14)
        self.label11.configure(text='Exchange Correlation (PBE0 and HSE06 are for EXX)')
        self.label11.pack(side='left')
        self.XC_calcttk = ttk.Combobox(self.frame14)
        self.XC_calcttk.configure(values=('LDA', 'PBE', 'GLLBSC', 'revPBE', 'RPBE' , 'PBE0', 'HSE06'), state='readonly')
        self.XC_calcttk.pack(side='top')
        self.XC_calcttk.current(0)
        self.frame14.configure(height='200', width='200')
        self.frame14.pack(side='top')

        # Ground_convergence
        self.frameGround_convergence = ttk.Frame(self.labelframe2)
        self.labelGround_convergence = ttk.Label(self.frameGround_convergence)
        self.labelGround_convergence.configure(text='Convergence for ground calc ({} for def):')
        self.labelGround_convergence.pack(side='left')
        self.Ground_convergencettk = ttk.Entry(self.frameGround_convergence)
        self.Ground_convergencettk.delete('0', 'end')
        self.Ground_convergencettk.insert('0', '{}')
        self.Ground_convergencettk.pack(side='top')
        self.frameGround_convergence.configure(height='200', width='200')
        self.frameGround_convergence.pack(side='top')
        
        # Band_convergence
        self.frameBand_convergence = ttk.Frame(self.labelframe2)
        self.labelBand_convergence = ttk.Label(self.frameBand_convergence)
        self.labelBand_convergence.configure(text='Convergence for band calc ({} for def):')
        self.labelBand_convergence.pack(side='left')
        self.Band_convergencettk = ttk.Entry(self.frameBand_convergence)
        self.Band_convergencettk.delete('0', 'end')
        self.Band_convergencettk.insert('0', "{'bands':8}")
        self.Band_convergencettk.pack(side='top')
        self.frameBand_convergence.configure(height='200', width='200')
        self.frameBand_convergence.pack(side='top')
        
        # Occupation
        self.frameOccupation = ttk.Frame(self.labelframe2)
        self.labelOccupation = ttk.Label(self.frameOccupation)
        self.labelOccupation.configure(text='Occupation ({} for def):')
        self.labelOccupation.pack(side='left')
        self.Occupationttk = ttk.Entry(self.frameOccupation)
        self.Occupationttk.delete('0', 'end')
        self.Occupationttk.insert('0', "{'name': 'fermi-dirac', 'width': 0.05}")
        self.Occupationttk.pack(side='top')
        self.frameOccupation.configure(height='200', width='200')
        self.frameOccupation.pack(side='top')
        
        # DOS number of points
        self.frameDOS_npoints = ttk.Frame(self.labelframe2)
        self.labelDOS_npoints = ttk.Label(self.frameDOS_npoints)
        self.labelDOS_npoints.configure(text='DOS number of points')
        self.labelDOS_npoints.pack(side='left')
        self.DOS_npointsttk = ttk.Entry(self.frameDOS_npoints)
        self.DOS_npointsttk.delete('0', 'end')
        self.DOS_npointsttk.insert('0', '501')
        self.DOS_npointsttk.pack(side='top')
        self.frameDOS_npoints.configure(height='200', width='200')
        self.frameDOS_npoints.pack(side='top')

        # DOS smearing width
        self.frameDOS_width = ttk.Frame(self.labelframe2)
        self.labelDOS_width = ttk.Label(self.frameDOS_width)
        self.labelDOS_width.configure(text='DOS smearing (0.0 for tetrahedron)')
        self.labelDOS_width.pack(side='left')
        self.DOS_widthttk = ttk.Entry(self.frameDOS_width)
        self.DOS_widthttk.delete('0', 'end')
        self.DOS_widthttk.insert('0', '0.1')
        self.DOS_widthttk.pack(side='top')
        self.frameDOS_width.configure(height='200', width='200')
        self.frameDOS_width.pack(side='top')

        # Spin polarized?
        self.frame15 = ttk.Frame(self.labelframe2)
        self.Spin_calcttk = ttk.Checkbutton(self.frame15)
        Spin_calcvar = BooleanVar()
        self.Spin_calcttk.configure(variable = Spin_calcvar, onvalue=True, offvalue=False, text='Spin-polarized calculation')
        self.Spin_calcttk.pack(side='top')
        self.frame15.configure(height='200', width='200')
        self.frame15.pack(side='top')

        # Magmom_per_atom
        self.frameMagmom_per_atom = ttk.Frame(self.labelframe2)
        self.labelMagmom_per_atom = ttk.Label(self.frameMagmom_per_atom)
        self.labelMagmom_per_atom.configure(text='Magnetic moment per atom')
        self.labelMagmom_per_atom.pack(side='left')
        self.Magmom_per_atomttk = ttk.Entry(self.frameMagmom_per_atom)
        self.Magmom_per_atomttk.delete('0', 'end')
        self.Magmom_per_atomttk.insert('0', '1.0')
        self.Magmom_per_atomttk.pack(side='top')
        self.frameMagmom_per_atom.configure(height='200', width='200')
        self.frameMagmom_per_atom.pack(side='top')
        
        # Grid size
        self.frame16 = ttk.Frame(self.labelframe2)
        self.label13 = ttk.Label(self.frame16)
        self.label13.configure(text='Grid size for electron density calc')
        self.label13.pack(side='left')
        self.gridrefttk = ttk.Entry(self.frame16)
        self.gridrefttk.delete('0', 'end')
        self.gridrefttk.insert('0', '4')
        self.gridrefttk.pack(side='top')
        self.frame16.configure(height='200', width='200')
        self.frame16.pack(side='top')
        self.labelframe2.configure(height='200', text='Electronic Calculation Parameters', width='200')
        self.labelframe2.pack(side='left')
        # End labelframe2 ------------------------------------------
        
        # labelframe3: Optical Calculation Parameters --------------
        self.labelframe3 = ttk.Labelframe(self.frame5)

        # opttype
        self.frameopttype = ttk.Frame(self.labelframe3)
        self.labelopttype = ttk.Label(self.frameopttype)
        self.labelopttype.configure(text='Optical Calculation Method')
        self.labelopttype.pack(side='left')
        self.opttypettk = ttk.Combobox(self.frameopttype)
        self.opttypettk.configure(values=('BSE', 'RPA'), state='readonly')
        self.opttypettk.pack(side='top')
        self.opttypettk.current(0)
        self.frameopttype.configure(height='200', width='200')
        self.frameopttype.pack(side='top')
        
        # optshift
        self.frameoptshift = ttk.Frame(self.labelframe3)
        self.labeloptshift = ttk.Label(self.frameoptshift)
        self.labeloptshift.configure(text='Energy shifting in eV')
        self.labeloptshift.pack(side='left')
        self.optshiftttk = ttk.Entry(self.frameoptshift)
        self.optshiftttk.delete('0', 'end')
        self.optshiftttk.insert('0', '0.0')
        self.optshiftttk.pack(side='top')
        self.frameoptshift.configure(height='200', width='200')
        self.frameoptshift.pack(side='top')
        
        # optBSEvb
        self.frameoptBSEvb = ttk.Frame(self.labelframe3)
        self.labeloptBSEvb = ttk.Label(self.frameoptBSEvb)
        self.labeloptBSEvb.configure(text='Valance bands(use range()):')
        self.labeloptBSEvb.pack(side='left')
        self.optBSEvbttk = ttk.Entry(self.frameoptBSEvb)
        self.optBSEvbttk.delete('0', 'end')
        self.optBSEvbttk.insert('0', 'range(0,4)')
        self.optBSEvbttk.pack(side='top')
        self.frameoptBSEvb.configure(height='200', width='200')
        self.frameoptBSEvb.pack(side='top')
        
        # optBSEcb
        self.frameoptBSEcb = ttk.Frame(self.labelframe3)
        self.labeloptBSEcb = ttk.Label(self.frameoptBSEcb)
        self.labeloptBSEcb.configure(text='Conduction bands(use range()):')
        self.labeloptBSEcb.pack(side='left')
        self.optBSEcbttk = ttk.Entry(self.frameoptBSEcb)
        self.optBSEcbttk.delete('0', 'end')
        self.optBSEcbttk.insert('0', 'range(4,7)')
        self.optBSEcbttk.pack(side='top')
        self.frameoptBSEcb.configure(height='200', width='200')
        self.frameoptBSEcb.pack(side='top')
        
        # optBSEminEn
        self.frameoptBSEminEn = ttk.Frame(self.labelframe3)
        self.labeloptBSEminEn = ttk.Label(self.frameoptBSEminEn)
        self.labeloptBSEminEn.configure(text='Min. En. for BSE calc.')
        self.labeloptBSEminEn.pack(side='left')
        self.optBSEminEnttk = ttk.Entry(self.frameoptBSEminEn)
        self.optBSEminEnttk.delete('0', 'end')
        self.optBSEminEnttk.insert('0', '0.0')
        self.optBSEminEnttk.pack(side='top')
        self.frameoptBSEminEn.configure(height='200', width='200')
        self.frameoptBSEminEn.pack(side='top')
        
        # optBSEmaxEn
        self.frameoptBSEmaxEn = ttk.Frame(self.labelframe3)
        self.labeloptBSEmaxEn = ttk.Label(self.frameoptBSEmaxEn)
        self.labeloptBSEmaxEn.configure(text='Max. En. for BSE calc.')
        self.labeloptBSEmaxEn.pack(side='left')
        self.optBSEmaxEnttk = ttk.Entry(self.frameoptBSEmaxEn)
        self.optBSEmaxEnttk.delete('0', 'end')
        self.optBSEmaxEnttk.insert('0', '20.0')
        self.optBSEmaxEnttk.pack(side='top')
        self.frameoptBSEmaxEn.configure(height='200', width='200')
        self.frameoptBSEmaxEn.pack(side='top')
        
        # optBSEnumdata
        self.frameoptBSEnumdata = ttk.Frame(self.labelframe3)
        self.labeloptBSEnumdata = ttk.Label(self.frameoptBSEnumdata)
        self.labeloptBSEnumdata.configure(text='Number of data points')
        self.labeloptBSEnumdata.pack(side='left')
        self.optBSEnumdatattk = ttk.Entry(self.frameoptBSEnumdata)
        self.optBSEnumdatattk.delete('0', 'end')
        self.optBSEnumdatattk.insert('0', '1001')
        self.optBSEnumdatattk.pack(side='top')
        self.frameoptBSEnumdata.configure(height='200', width='200')
        self.frameoptBSEnumdata.pack(side='top')
        
        #num_of_bands
        self.frame17 = ttk.Frame(self.labelframe3)
        self.label14 = ttk.Label(self.frame17)
        self.label14.configure(text='Number of bands')
        self.label14.pack(side='left')
        self.num_of_bandsttk = ttk.Entry(self.frame17)
        self.num_of_bandsttk.delete('0', 'end')
        self.num_of_bandsttk.insert('0', '16')
        self.num_of_bandsttk.pack(side='top')
        self.frame17.configure(height='200', width='200')
        self.frame17.pack(side='top')

        #optFDsmear
        self.frame18 = ttk.Frame(self.labelframe3)
        self.label15 = ttk.Label(self.frame18)
        self.label15.configure(text='Fermi-Dirac smearing value')
        self.label15.pack(side='left')
        self.optFDsmearttk = ttk.Entry(self.frame18)
        self.optFDsmearttk.delete('0', 'end')
        self.optFDsmearttk.insert('0', '0.05')
        self.optFDsmearttk.pack(side='top')
        self.frame18.configure(height='200', width='200')
        self.frame18.pack(side='top')

        #opteta
        self.frame19 = ttk.Frame(self.labelframe3)
        self.label16 = ttk.Label(self.frame19)
        self.label16.configure(text='Eta value')
        self.label16.pack(side='left')
        self.optetattk = ttk.Entry(self.frame19)
        self.optetattk.delete('0', 'end')
        self.optetattk.insert('0', '0.05')
        self.optetattk.pack(side='top')
        self.frame19.configure(height='200', width='200')
        self.frame19.pack(side='top')

        #optdomega0
        self.frame20 = ttk.Frame(self.labelframe3)
        self.label17 = ttk.Label(self.frame20)
        self.label17.configure(text='Domega0 value')
        self.label17.pack(side='left')
        self.optdomega0ttk = ttk.Entry(self.frame20)
        self.optdomega0ttk.delete('0', 'end')
        self.optdomega0ttk.insert('0', '0.02')
        self.optdomega0ttk.pack(side='top')
        self.frame20.configure(height='200', width='200')
        self.frame20.pack(side='top')

        #optnblocks
        self.frame21 = ttk.Frame(self.labelframe3)
        self.label18 = ttk.Label(self.frame21)
        self.label18.configure(text='n-blocks number')
        self.label18.pack(side='left')
        self.optnblocksttk = ttk.Entry(self.frame21)
        self.optnblocksttk.delete('0', 'end')
        self.optnblocksttk.insert('0', '4')
        self.optnblocksttk.pack(side='top')
        self.frame21.configure(height='200', width='200')
        self.frame21.pack(side='top')

        #optomega2
        self.frameoptomega2 = ttk.Frame(self.labelframe3)
        self.labeloptomega2 = ttk.Label(self.frameoptomega2)
        self.labeloptomega2.configure(text='omega2')
        self.labeloptomega2.pack(side='left')
        self.optomega2ttk = ttk.Entry(self.frameoptomega2)
        self.optomega2ttk.delete('0', 'end')
        self.optomega2ttk.insert('0', '0.05')
        self.optomega2ttk.pack(side='top')
        self.frameoptomega2.configure(height='200', width='200')
        self.frameoptomega2.pack(side='top')
        
        #optecut
        self.frameoptecut = ttk.Frame(self.labelframe3)
        self.labeloptecut = ttk.Label(self.frameoptecut)
        self.labeloptecut.configure(text='Cut-off en. for opt.')
        self.labeloptecut.pack(side='left')
        self.optecutttk = ttk.Entry(self.frameoptecut)
        self.optecutttk.delete('0', 'end')
        self.optecutttk.insert('0', '100')
        self.optecutttk.pack(side='top')
        self.frameoptecut.configure(height='200', width='200')
        self.frameoptecut.pack(side='top')
        
        self.labelframe3.configure(height='200', text='Optical Calculation Parameters', width='200')
        self.labelframe3.pack(side='left')
        self.frame5.configure(height='200', width='200')
        self.frame5.pack(side='top')
        # End labelframe3 ------------------------------------------
        
        # labelframe4: Frame for strain-shear ----------------------
        self.frame13 = ttk.Frame(self.frame4)
        self.labelframe4 = ttk.Labelframe(self.frame13)
        self.frame22 = ttk.Frame(self.labelframe4)
        self.EpsXttk = ttk.Checkbutton(self.frame22)
        EpsXvar = BooleanVar()
        self.EpsXttk.configure(variable = EpsXvar, onvalue=True, offvalue=False, text='EpsX')
        self.EpsXttk.pack(side='top')
        self.EpsYttk = ttk.Checkbutton(self.frame22)
        EpsYvar = BooleanVar()
        self.EpsYttk.configure(variable = EpsYvar, onvalue=True, offvalue=False, text='EpsY')
        self.EpsYttk.pack(side='top')
        self.EpsZttk = ttk.Checkbutton(self.frame22)
        EpsZvar = BooleanVar()
        self.EpsZttk.configure(variable = EpsZvar, onvalue=True, offvalue=False, text='EpsZ')
        self.EpsZttk.pack(side='top')
        self.ShearYZttk = ttk.Checkbutton(self.frame22)
        ShearYZvar = BooleanVar()
        self.ShearYZttk.configure(variable = ShearYZvar, onvalue=True, offvalue=False, text='ShearYZ')
        self.ShearYZttk.pack(side='top')
        self.ShearXZttk = ttk.Checkbutton(self.frame22)
        ShearXZvar = BooleanVar()
        self.ShearXZttk.configure(variable = ShearXZvar, onvalue=True, offvalue=False, text='ShearXZ')
        self.ShearXZttk.pack(side='top')
        self.ShearXYttk = ttk.Checkbutton(self.frame22)
        ShearXYvar = BooleanVar()
        self.ShearXYttk.configure(variable = ShearXYvar, onvalue=True, offvalue=False, text='ShearXY')
        self.ShearXYttk.pack(side='top')
        self.frame22.configure(height='200', width='200')
        self.frame22.pack(side='top')
        self.labelframe4.configure(height='200', text='Strain Relaxation', width='200')
        self.labelframe4.pack(side='left')
        # End labelframe4 ------------------------------------------------
        
        # GWframe: Frame for GW parameters -------------------------------
        self.GWframe = ttk.Frame(self.frame4)
        self.labelGWframe = ttk.Labelframe(self.GWframe)

        # GWtype
        self.frameGWtype = ttk.Frame(self.labelGWframe)
        self.labelGWtype = ttk.Label(self.frameGWtype)
        self.labelGWtype.configure(text='GW type')
        self.labelGWtype.pack(side='left')
        self.GWtypettk = ttk.Combobox(self.frameGWtype)
        self.GWtypettk.configure(values=('GW0', 'G0W0'), state='readonly')
        self.GWtypettk.pack(side='top')
        self.GWtypettk.current(0)
        self.frameGWtype.configure(height='200', width='200')
        self.frameGWtype.pack(side='top')

        # GWkpoints
        self.frameGWkpoints = ttk.Frame(self.labelGWframe)
        self.labelGWkpoints = ttk.Label(self.frameGWkpoints)
        self.labelGWkpoints.configure(text='GW K-points change as list [[kix,kiy,kiz],...]')
        self.labelGWkpoints.pack(side='left')
        self.GWkpointsttk = tk.Entry(self.frameGWkpoints)
        self.GWkpointsttk.delete('0', 'end')
        self.GWkpointsttk.insert('0', '[[0.0,0.0,0.0]]')
        self.GWkpointsttk.pack(side='top')
        self.frameGWkpoints.configure(height='200', width='200')
        self.frameGWkpoints.pack(side='top')

        # GWtruncation
        self.frameGWtruncation = ttk.Frame(self.labelGWframe)
        self.labelGWtruncation = ttk.Label(self.frameGWtruncation)
        self.labelGWtruncation.configure(text='GW truncation')
        self.labelGWtruncation.pack(side='left')
        self.GWtruncationttk = ttk.Combobox(self.frameGWtruncation)
        self.GWtruncationttk.configure(values=(None, '2D', '1D', '0D', 'wigner-seitz'), state='readonly')
        self.GWtruncationttk.pack(side='top')
        self.GWtruncationttk.current(4)
        self.frameGWtruncation.configure(height='200', width='200')
        self.frameGWtruncation.pack(side='top')

        # GWcut_off_energy
        self.frameGWcut_off_energy = ttk.Frame(self.labelGWframe)
        self.labelGWcut_off_energy = ttk.Label(self.frameGWcut_off_energy)
        self.labelGWcut_off_energy.configure(text='Cut-off en. for opt.')
        self.labelGWcut_off_energy.pack(side='left')
        self.GWcut_off_energyttk = ttk.Entry(self.frameGWcut_off_energy)
        self.GWcut_off_energyttk.delete('0', 'end')
        self.GWcut_off_energyttk.insert('0', '100')
        self.GWcut_off_energyttk.pack(side='top')
        self.frameGWcut_off_energy.configure(height='200', width='200')
        self.frameGWcut_off_energy.pack(side='top')

        # GWbandVB
        self.frameGWbandVB = ttk.Frame(self.labelGWframe)
        self.labelGWbandVB = ttk.Label(self.frameGWbandVB)
        self.labelGWbandVB.configure(text='Valence band number')
        self.labelGWbandVB.pack(side='left')
        self.GWbandVBttk = ttk.Entry(self.frameGWbandVB)
        self.GWbandVBttk.delete('0', 'end')
        self.GWbandVBttk.insert('0', '8')
        self.GWbandVBttk.pack(side='top')
        self.frameGWbandVB.configure(height='200', width='200')
        self.frameGWbandVB.pack(side='top')

        # GWbandCB
        self.frameGWbandCB = ttk.Frame(self.labelGWframe)
        self.labelGWbandCB = ttk.Label(self.frameGWbandCB)
        self.labelGWbandCB.configure(text='Conduction band number')
        self.labelGWbandCB.pack(side='left')
        self.GWbandCBttk = ttk.Entry(self.frameGWbandCB)
        self.GWbandCBttk.delete('0', 'end')
        self.GWbandCBttk.insert('0', '8')
        self.GWbandCBttk.pack(side='top')
        self.frameGWbandCB.configure(height='200', width='200')
        self.frameGWbandCB.pack(side='top')

        # GWppa
        self.GWppattk = ttk.Checkbutton(self.labelGWframe)
        GWppavar = BooleanVar()
        self.GWppattk.configure(variable = GWppavar, onvalue=True, offvalue=False, text='Plasmon Pole Approximation')
        self.GWppattk.pack(side='top')

        # GWq0correction
        self.GWq0correctionttk = ttk.Checkbutton(self.labelGWframe)
        GWq0correctionvar = BooleanVar()
        self.GWq0correctionttk.configure(variable = GWq0correctionvar, onvalue=True, offvalue=False, text='Analytic correction to the q=0 contribution')
        self.GWq0correctionttk.pack(side='top')

        # GWnblock
        self.GWnblockttk = ttk.Checkbutton(self.labelGWframe)
        GWnblockvar = BooleanVar()
        self.GWnblockttk.configure(variable = GWnblockvar, onvalue=True, offvalue=False, text='Cuts chi0 into as many blocks to reduce mem.')
        self.GWnblockttk.pack(side='top')

        # GWbandinterpolation
        self.GWbandinterpolationttk = ttk.Checkbutton(self.labelGWframe)
        GWbandinterpolationvar = BooleanVar()
        self.GWbandinterpolationttk.configure(variable = GWbandinterpolationvar, onvalue=True, offvalue=False, text='Spline draw fpr bands? (needs min. 3 points)')
        self.GWbandinterpolationttk.pack(side='top')
        
        self.labelGWframe.configure(height='200', text='GW Parameters (Only applicable when Basis = PW-GW', width='200')
        self.labelGWframe.pack(side='left')
        self.GWframe.configure(height='200', width='200')
        self.GWframe.pack(side='left')
        # End GWframe ---------------------------------------------
        
        # labelframe5: Other Parameters ---------------------------
        self.labelframe5 = ttk.Labelframe(self.frame13)

        # Restart calculation
        self.restartttk = ttk.Checkbutton(self.labelframe5)
        restartvar = BooleanVar()
        self.restartttk.configure(variable = restartvar, onvalue=True, offvalue=False, text='Restart calculation from file')
        self.restartttk.pack(side='top')
        
        self.labelframe5.configure(height='200', text='General options', width='200')
        self.labelframe5.pack(side='top')
        self.frame13.configure(height='200', width='200')
        self.frame13.pack(side='left')
        self.frame4.configure(height='200', width='200')
        self.frame4.pack(side='top')
        # End labelframe5 -------------------------------------------
        
        self.notebookUpper.add(self.frame4, state='normal', text='Input Parameters')
        
        # ------------- Calculate tab -----------------
        self.frame3 = ttk.Frame(self.notebookUpper)
        
        # MPI core number
        self.frame25 = ttk.Frame(self.frame3)
        self.label21 = ttk.Label(self.frame25)
        self.label21.configure(text='MPI core number')
        self.label21.pack(side='left')
        self.MPIcoresttk = ttk.Entry(self.frame25)
        self.MPIcoresttk.delete('0', 'end')
        self.MPIcoresttk.insert('0', '1')
        self.MPIcoresttk.pack(side='top')
        self.frame25.configure(height='200', width='200')
        self.frame25.pack(side='top')
        
        # Start calculation
        self.frame26 = ttk.Frame(self.frame3)
        self.button3 = ttk.Button(self.frame26)
        self.button3.configure(text='Start calculation')
        self.button3.pack(side='top')
        self.button3.configure(command=onCalculate)
        self.frame26.configure(height='200', width='200')
        self.frame26.pack(side='top')
        
        # Log text box
        self.frame27 = ttk.Frame(self.frame3)
        self.text4 = tk.Text(self.frame27)
        self.text4.configure(height='50', width='120')
        self.text4.insert('0.0', 'gpawsolve.py stdout log: \n')
        self.text4.pack(side='top')
        self.frame27.configure(height='200', width='200')
        self.frame27.pack(side='top')
        
        self.frame3.configure(height='200', width='200')
        self.frame3.pack(side='top')
        self.notebookUpper.add(self.frame3, text='Calculate')

        # --------------- About box -------------------
        self.frame24 = ttk.Frame(self.notebookUpper)
        self.text2 = tk.Text(self.frame24)
        self.text2.configure(background='#4f4f4f', foreground='#ffffff', height='14', undo='false')
        self.text2.configure(width='60', wrap='char')
        _text_ = '''GG (gpaw-tools & gui)
=======================
GG is a graphical user interface (GUI) for a 
gpawsolve.py script, which aims simple and
expediting calculations with GPAW/ASE codes.

For licensing information, please refer to LICENSE file.'''
        self.text2.insert('0.0', _text_)
        self.text2.pack(side='left')
        self.button1 = ttk.Button(self.frame24, text='gpaw-tools website', command=lambda aurl=url:OpenUrl(aurl))
        self.gg_fullsmall_png = tk.PhotoImage(file=os.path.join(PROJECT_PATH,'gui_files/gpaw-tools.png'))
        self.button1.configure(image=self.gg_fullsmall_png, state='normal')
        self.button1.pack(side='left')
        self.frame24.configure(height='200', width='900')
        self.frame24.pack(side='top')
        self.notebookUpper.add(self.frame24, text='About')
        self.notebookUpper.configure(height='600', width='900')
        self.notebookUpper.pack(fill='x', side='top')
        
        # Message log
        self.notebookBottom = ttk.Notebook(self.frame2)
        self.text1 = tk.Text(self.notebookBottom)
        self.text1.configure(background='#000000', foreground='#ffffff', height='10', width='50')
        _text_ = '''Program started.\n'''
        self.text1.insert('0.0', _text_)
        self.text1.pack(side='top')
        self.notebookBottom.add(self.text1, text='Message Log')
        self.notebookBottom.configure(height='100', width='900')
        self.notebookBottom.pack(fill='x', side='top')
        self.frame2.configure(height='800', width='900')
        self.frame2.pack(fill='both', side='top')
        self.gg_png = tk.PhotoImage(file=os.path.join(PROJECT_PATH,'gui_files/gpaw-tools.png'))
        self.toplevel1.configure(height='800', width='900')
        self.toplevel1.iconphoto(True, self.gg_png)
        self.toplevel1.resizable(False, False)
        self.toplevel1.title('gpaw-tools GUI')

        # Main widget
        self.mainwindow = self.toplevel1


    def run(self):
        '''Running the mainloop'''
        self.mainwindow.mainloop()

if __name__ == '__main__':
    app = gg()
    app.run()
