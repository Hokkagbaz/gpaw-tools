'''
optimize_cutoff.py: Sample Cut-off Energy Optimization with GPAW

Usage: $ gpaw -P<core_number> python optimize_cutoff.py
'''
from ase import *
from gpaw import GPAW, PW
from ase.parallel import paropen, world, parprint

#-------------------------------------------------------------
# ENTER PARAMETERS
# -------------------------------------------------------------
cutoff_min = 200
cutoff_max = 400
cutoff_step = 50

kpts_x = 7
kpts_y = 7
kpts_z = 7

# -------------------------------------------------------------
# Bulk Configuration
# -------------------------------------------------------------
bulk_configuration = Atoms(
    [
    Atom('Si', ( 0.0, 0.0, 0.0 )),
    Atom('Si', ( 1.35765, 1.35765, 1.35765 )),
    ],
    cell=[(0.0, 2.7153, 2.7153), (2.7153, 0.0, 2.7153), (2.7153, 2.7153, 0.0)],
    pbc=True,
    )
# -------------------------------------------------------------
# DO NOT NEED TO CHANGE ANYTHING UNDER THIS POINT
# -------------------------------------------------------------
with paropen('OptimizeCutOff_Table-CutOff.txt', 'a') as f:
    f.write('CutOff_Energy  Total_Energy\n')
    for ecut in range(cutoff_min, cutoff_max+1, cutoff_step):
        bulk_configuration.calc = GPAW(mode=PW(ecut),
                                    xc='PBE',
                                    kpts=(kpts_x, kpts_y, kpts_z),
                                    parallel={'domain': world.size},
                                    basis='dzp',
                                    txt='OptimizeCutOff_%d.txt' % ecut)
        parprint ("CutOff_energy:"+str(ecut)+"  Potential_Energy:"+str(bulk_configuration.get_potential_energy()))
        f.write(str(ecut)+'  '+str(bulk_configuration.get_potential_energy())+'\n')
