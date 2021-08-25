import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, ttk, font, BooleanVar, StringVar
import os, sys, io
import pathlib
import subprocess
from subprocess import Popen
import pygubu
from shlex import split
from ase.io import read, write

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_UI = os.path.join(PROJECT_PATH, "gg.ui")

# gg.py: GUI for gpawsolve.py
# ----------------------------
    
class gg:
    def __init__(self, master=None):
        global DOS_calcvar, Band_calcvar, Density_calcvar, Optical_calcvar, Spin_calcvar, EpsXvar, EpsYvar, EpsZvar, ShearYZvar, ShearXZvar, ShearXYvar, WantCIFexportvar
        
        def onOpen():
            global basename
            textfile = filedialog.askopenfilename(initialdir = PROJECT_PATH, title = "Open file", filetypes = (("CIF files","*.cif"),("All files","*.*")))
            textfilenamepath = textfile
            basename = StringVar()
            print(basename)
            basename = pathlib.Path(textfilenamepath).stem
            #textfile.close()
            self.text1.insert(tk.END, "File opened: "+basename+" \n")
            # Opening a working directory
            if not os.path.isdir(basename):
                os.makedirs(basename, exist_ok=True)
            print(basename)    
            asestruct = read(textfilenamepath, index='-1')
            write(os.path.join(os.path.join(PROJECT_PATH, basename), basename)+'_InitialStructure.png', asestruct)
            self.structureimage = tk.PhotoImage(file=os.path.join(os.path.join(PROJECT_PATH, basename), basename)+'_InitialStructure.png')
            self.button2.configure(image=self.structureimage, style='Toolbutton', text='button2')
            # Loading config file
            import config
            # There must be some elegant way to do this.
            if config.Use_PW == True:
                self.Use_PWttk.current(0)
            else:
                self.Use_PWttk.current(1)
            
            if config.DOS_calc == True:
                DOS_calcvar.set(True)
            else:
                DOS_calcvar.set(False)
            
            if config.Band_calc == True:
                Band_calcvar.set(True)
            else:
                Band_calcvar.set(False)
            
            if config.Density_calc == True:
                Density_calcvar.set(True)
            else:
                Density_calcvar.set(False)
            
            if config.Optical_calc == True:
                Optical_calcvar.set(True)
            else:
                Optical_calcvar.set(False)
                
            self.fmaxvalttk.delete('0', 'end')
            self.fmaxvalttk.insert('0', config.fmaxval)
            
            self.cut_off_energyttk.delete('0', 'end')
            self.cut_off_energyttk.insert('0', config.cut_off_energy)
            
            self.kpts_xttk.delete('0', 'end')
            self.kpts_xttk.insert('0', config.kpts_x)
            self.kpts_yttk.delete('0', 'end')
            self.kpts_yttk.insert('0', config.kpts_y)
            self.kpts_zttk.delete('0', 'end')
            self.kpts_zttk.insert('0', config.kpts_z)
            
            self.band_pathttk.delete('0', 'end')
            self.band_pathttk.insert('0', config.band_path)

            self.band_npointsttk.delete('0', 'end')
            self.band_npointsttk.insert('0', config.band_npoints)

            self.energy_maxttk.delete('0', 'end')
            self.energy_maxttk.insert('0', config.energy_max)
            
            if config.XC_calc == 'LDA':
                self.XC_calcttk.current(0)
            elif config.XC_calc == 'PBE':
                self.XC_calcttk.current(1)
            elif config.XC_calc == 'revPBE':
                self.XC_calcttk.current(2)
            elif config.XC_calc == 'RPBE':
                self.XC_calcttk.current(3)
            else:
                self.XC_calcttk.current(0)
                
            if config.Spin_calc == True:
                Spin_calcvar.set(True)
            else:
                Spin_calcvar.set(False)

            self.gridrefttk.delete('0', 'end')
            self.gridrefttk.insert('0', config.gridref)             

            self.num_of_bandsttk.delete('0', 'end')
            self.num_of_bandsttk.insert('0', config.num_of_bands)
            
            self.optFDsmearttk.delete('0', 'end')
            self.optFDsmearttk.insert('0', config.optFDsmear)
            
            self.optetattk.delete('0', 'end')
            self.optetattk.insert('0', config.opteta)
            
            self.optdomega0ttk.delete('0', 'end')
            self.optdomega0ttk.insert('0', config.optdomega0)
            
            self.optnblocksttk.delete('0', 'end')
            self.optnblocksttk.insert('0', config.optnblocks)
            
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

            if config.WantCIFexport == True:
                WantCIFexportvar.set(True)
            else:
                WantCIFexportvar.set(False)

            self.MPIcoresttk.delete('0', 'end')
            self.MPIcoresttk.insert('0', config.MPIcores)
            
            self.text1.insert(tk.END, "Configuration loaded, please continue with Input parameters tab \n")
            
        def onCalculate():
            #Firstly, lets save all options to config file.
            f1 = open('config.py', 'w')

            if self.Use_PWttk.get() == 'PW':
                print("Use_PW = True", end="\n", file=f1)
            else:
                print("Use_PW = False", end="\n", file=f1)
            
            print("DOS_calc = "+ str(DOS_calcvar.get()), end="\n", file=f1)
            print("Band_calc = "+ str(Band_calcvar.get()), end="\n", file=f1)
            print("Density_calc = "+ str(Density_calcvar.get()), end="\n", file=f1)
            print("Optical_calc = "+ str(Optical_calcvar.get()), end="\n", file=f1)
            print("fmaxval = "+ str(self.fmaxvalttk.get()), end="\n", file=f1)
            print("cut_off_energy = "+ str(self.cut_off_energyttk.get()), end="\n", file=f1)
            print("kpts_x = "+ str(self.kpts_xttk.get()), end="\n", file=f1)
            print("kpts_y = "+ str(self.kpts_yttk.get()), end="\n", file=f1)
            print("kpts_z = "+ str(self.kpts_zttk.get()), end="\n", file=f1)
            print("band_path = '"+ str(self.band_pathttk.get())+"'", end="\n", file=f1)
            print("band_npoints = "+ str(self.band_npointsttk.get()), end="\n", file=f1)
            print("energy_max = "+ str(self.energy_maxttk.get()), end="\n", file=f1)
            
            if self.XC_calcttk.get() == 'LDA':
                print("XC_calc = 'LDA'", end="\n", file=f1)
            elif self.XC_calcttk.get() == 'PBE':
                print("XC_calc = 'PBE'", end="\n", file=f1)
            elif self.XC_calcttk.get() == 'revPBE':
                print("XC_calc = 'revPBE'", end="\n", file=f1)
            elif self.XC_calcttk.get() == 'RPBE':
                print("XC_calc = 'RPBE'", end="\n", file=f1)
            else:
                print("XC_calc = 'LDA'", end="\n", file=f1)
            
            print("Spin_calc = "+ str(Spin_calcvar.get()), end="\n", file=f1)
            print("gridref = "+ str(self.gridrefttk.get()), end="\n", file=f1)
            print("num_of_bands = "+ str(self.num_of_bandsttk.get()), end="\n", file=f1)
            print("optFDsmear = "+ str(self.optFDsmearttk.get()), end="\n", file=f1)
            print("opteta = "+ str(self.optetattk.get()), end="\n", file=f1)
            print("optdomega0 = "+ str(self.optdomega0ttk.get()), end="\n", file=f1)
            print("optnblocks = "+ str(self.optnblocksttk.get()), end="\n", file=f1)
            print("draw_graphs = True", end="\n", file=f1)
            print("whichstrain = ["+str(EpsXvar.get())+", "+str(EpsYvar.get())+", "+str(EpsZvar.get())+", "+str(ShearYZvar.get())+", "+str(ShearXZvar.get())+", "+str(ShearXYvar.get())+"]", end="\n", file=f1)
            print("WantCIFexport = "+ str(WantCIFexportvar.get()), end="\n", file=f1)
            print("MPIcores = "+ str(self.MPIcoresttk.get()), end="\n", file=f1)
            f1.close()
            
            #Running the gpawsolve
            #proc = subprocess.Popen(['gpaw -P '+str(self.MPIcoresttk.get())+' python gpawsolve.py -oci '+str(basename)+'.cif'], shell = True, stdout=subprocess.PIPE)
            gpawcommand = 'gpaw -P '+str(self.MPIcoresttk.get())+' python gpawsolve.py -oci '+str(basename)+'.cif'
            #gpawcommand = 'gpaw python gpawsolve.py -oci '+str(basename)+'.cif'
            proc = Popen(split(gpawcommand), shell=False, stdout = subprocess.PIPE)
            #proc = subprocess.Popen(['ls -al'], shell = True, stdout=subprocess.PIPE)
            self.text1.insert(tk.END, "Command executed: "+gpawcommand+" \n")
            # Save stdout as a log 
            f2 = open(os.path.join(os.path.join(PROJECT_PATH, basename), basename)+"-STDOUT-Log.txt", 'w')
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):  # or another encoding
                # do something with line
                self.text4.insert(tk.END, line)
                print(line, end="\n", file=f2)
            self.text1.insert(tk.END, "Calculation finished... \n")
            f2.close()
            self.text1.insert(tk.END, "STDOUT is also saved as log file. \n")
            
            asestruct = read(os.path.join(os.path.join(PROJECT_PATH, basename), basename)+"-Final.cif", index='-1')
            write(os.path.join(os.path.join(PROJECT_PATH, basename), basename)+'_FinalStructure.png', asestruct)
            proc = Popen(split('mv '+basename+'_FinalStructure.png '+basename), shell=False)
            self.text1.insert(tk.END, "Initial and Final Structure PNG files are saved to "+basename+" folder \n")
            
            
        # build ui
        self.toplevel1 = tk.Tk() if master is None else tk.Toplevel(master)
        self.frame2 = ttk.Frame(self.toplevel1)
        self.notebookUpper = ttk.Notebook(self.frame2)
        self.frame1 = ttk.Frame(self.notebookUpper)
        self.loadCIFfilettk = ttk.Button(self.frame1)
        self.loadCIFfilettk.configure(state='normal', text='Load CIF File')
        self.loadCIFfilettk.pack(pady='10', side='top')
        self.loadCIFfilettk.configure(command=onOpen)
        self.button2 = ttk.Button(self.frame1)
        self.structureimage = tk.PhotoImage(file='gui_files/gg_full.png')
        self.button2.configure(image=self.structureimage, style='Toolbutton', text='button2')
        self.button2.pack(side='top')
        self.frame1.configure(height='200', width='200')
        self.frame1.pack(side='top')
        self.notebookUpper.add(self.frame1, text='Load Structure')
        self.frame4 = ttk.Frame(self.notebookUpper)
        self.frame5 = ttk.Frame(self.frame4)
        self.labelframe1 = ttk.Labelframe(self.frame5)
        self.frame6 = ttk.Frame(self.labelframe1)
        self.label1 = ttk.Label(self.frame6)
        self.label1.configure(text='Calculator')
        self.label1.pack(side='left')
        self.Use_PWttk = ttk.Combobox(self.frame6)
        self.Use_PWttk.configure(values=('PW', 'LCAO'), state='readonly')
        self.Use_PWttk.pack(side='top')
        self.Use_PWttk.current(0)
        self.frame6.configure(height='200', width='200')
        self.frame6.pack(side='top')
        # Setting DOS_calc related checkbutton
        self.DOS_calcttk = ttk.Checkbutton(self.labelframe1)
        DOS_calcvar = BooleanVar()
        self.DOS_calcttk.configure(state='normal', variable = DOS_calcvar, onvalue=True, offvalue=False, takefocus=False, text='DOS Calculation')
        self.DOS_calcttk.pack(side='top')
        self.Band_calcttk = ttk.Checkbutton(self.labelframe1)
        Band_calcvar = BooleanVar()
        self.Band_calcttk.configure(variable = Band_calcvar, onvalue=True, offvalue=False, text='Band Structure Calculation')
        self.Band_calcttk.pack(side='top')
        self.Density_calcttk = ttk.Checkbutton(self.labelframe1)
        Density_calcvar = BooleanVar()
        self.Density_calcttk.configure(variable = Density_calcvar, onvalue=True, offvalue=False,text='All-Electron Density Calculation')
        self.Density_calcttk.pack(side='top')
        self.checkbutton4 = ttk.Checkbutton(self.labelframe1)
        Optical_calcvar = BooleanVar()
        self.checkbutton4.configure(variable = Optical_calcvar, onvalue=True, offvalue=False, text='Optical Properties Calculation')
        self.checkbutton4.pack(side='top')
        self.labelframe1.configure(height='200', text='Calculator Settings', width='200')
        self.labelframe1.pack(side='left')
        self.labelframe2 = ttk.Labelframe(self.frame5)
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
        self.frame14 = ttk.Frame(self.labelframe2)
        self.label11 = ttk.Label(self.frame14)
        self.label11.configure(text='Exchange Correlation')
        self.label11.pack(side='left')
        
        self.XC_calcttk = ttk.Combobox(self.frame14)
        self.XC_calcttk.configure(values=('LDA', 'PBE', 'revPBE', 'RPBE'), state='readonly')
        self.XC_calcttk.pack(side='top')
        self.XC_calcttk.current(0)
        
        self.frame14.configure(height='200', width='200')
        self.frame14.pack(side='top')
        self.frame15 = ttk.Frame(self.labelframe2)
        self.Spin_calcttk = ttk.Checkbutton(self.frame15)
        Spin_calcvar = BooleanVar()
        self.Spin_calcttk.configure(variable = Spin_calcvar, onvalue=True, offvalue=False, text='Spin-polarized calculation')
        self.Spin_calcttk.pack(side='top')
        self.frame15.configure(height='200', width='200')
        self.frame15.pack(side='top')
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
        self.labelframe3 = ttk.Labelframe(self.frame5)
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
        self.labelframe3.configure(height='200', text='Optical Calculation Parameters', width='200')
        self.labelframe3.pack(side='left')
        self.frame5.configure(height='200', width='200')
        self.frame5.pack(side='top')
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
        self.labelframe5 = ttk.Labelframe(self.frame13)
        self.WantCIFexportttk = ttk.Checkbutton(self.labelframe5)
        WantCIFexportvar = BooleanVar()
        self.WantCIFexportttk.configure(variable = WantCIFexportvar, onvalue=True, offvalue=False, text='CIF export for the final structure')
        self.WantCIFexportttk.pack(side='top')
        self.labelframe5.configure(height='200', text='General options', width='200')
        self.labelframe5.pack(side='top')
        self.frame13.configure(height='200', width='200')
        self.frame13.pack(side='left')
        self.frame4.configure(height='200', width='200')
        self.frame4.pack(side='top')
        self.notebookUpper.add(self.frame4, state='normal', text='Input Parameters')
        self.frame3 = ttk.Frame(self.notebookUpper)
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
        self.frame26 = ttk.Frame(self.frame3)
        self.button3 = ttk.Button(self.frame26)
        self.button3.configure(text='Start calculation')
        self.button3.pack(side='top')
        self.button3.configure(command=onCalculate)
        self.frame26.configure(height='200', width='200')
        self.frame26.pack(side='top')
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
        self.frame24 = ttk.Frame(self.notebookUpper)
        self.text2 = tk.Text(self.frame24)
        self.text2.configure(background='#4f4f4f', foreground='#ffffff', height='14', undo='false')
        self.text2.configure(width='60', wrap='char')
        _text_ = '''GG ([g]paw-tools [g]ui)
=======================
GG is a graphical user interface (GUI) for a 
gpawsolve.py script, which aims simple and
expediting calculations with GPAW/ASE codes.

Copyrighted with MIT license by
Sefer Bora Lisesivdin and Beyza Lisesivdin

For more information, please refer to LICENSE file.'''
        self.text2.insert('0.0', _text_)
        self.text2.pack(side='left')
        self.button1 = ttk.Button(self.frame24)
        self.gg_fullsmall_png = tk.PhotoImage(file='gui_files/gg_fullsmall.png')
        self.button1.configure(image=self.gg_fullsmall_png, state='normal', text='button1')
        self.button1.pack(side='left')
        self.frame24.configure(height='200', width='900')
        self.frame24.pack(side='top')
        self.notebookUpper.add(self.frame24, text='About')
        self.notebookUpper.configure(height='500', width='900')
        self.notebookUpper.pack(fill='x', side='top')
        self.notebookBottom = ttk.Notebook(self.frame2)
        self.text1 = tk.Text(self.notebookBottom)
        self.text1.configure(background='#000000', foreground='#ffffff', height='10', width='50')
        _text_ = '''Program started.\n'''
        self.text1.insert('0.0', _text_)
        self.text1.pack(side='top')
        self.notebookBottom.add(self.text1, text='Message Log')
        self.notebookBottom.configure(height='100', width='900')
        self.notebookBottom.pack(fill='x', side='top')
        self.frame2.configure(height='600', width='900')
        self.frame2.pack(fill='both', side='top')
        self.gg_png = tk.PhotoImage(file='gui_files/gg.png')
        self.toplevel1.configure(height='600', width='900')
        self.toplevel1.iconphoto(True, self.gg_png)
        self.toplevel1.resizable(False, False)
        self.toplevel1.title('gpaw-tools GUI')

        # Main widget
        self.mainwindow = self.toplevel1
    

    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = gg()
    app.run()
