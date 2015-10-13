from src.main.common import Matrix
from src.main.fileinput import FileInputBasis, FileInputNuclei
from src.main.matrixelements import DensityMatrixElement, KineticEnergyIntegral, NuclearAttractionIntegral, OverlapIntegral
from src.main.selfconsistentfield import TotalEnergy, SCFProcedure, CoulombsLaw, CoulombsLawArray

import numpy as np
import time


if __name__ == '__main__':
    np.set_printoptions(linewidth=10000)

    start = time.clock()
    print('*********************************************************************************************************')
    print('\nA BASIC QUANTUM CHEMICAL PROGRAM IN PYTHON\n\n')

    nuclei_array = FileInputNuclei('HeH+.mol').create_nuclei_array()
    electrons = FileInputNuclei('HeH+.mol').electron_count()
    basis_set_array = FileInputBasis('STO-3G-edited.gbs', nuclei_array).create_basis_set_array()

    nuclei_name_list = [x.get_name() for x in nuclei_array]
    print(nuclei_name_list)

    coulomb_law_array = CoulombsLawArray(CoulombsLaw, nuclei_array).calculate_total_electric_potential_energy()
    nuclear_repulsion_energy = coulomb_law_array.sum() / 2
    print('\nNUCLEAR REPULSION ARRAY')
    print(coulomb_law_array)
    print('Total Nuclear-Nuclear Potential Energy: ' + str(nuclear_repulsion_energy) + ' a.u.')

    print('\n*********************************************************************************************************')

    matrix = Matrix(len(basis_set_array))
    s_matrix = matrix.create_matrix(OverlapIntegral(basis_set_array))
    print('\nOrbital Overlap Matrix')
    print(s_matrix)
    t_matrix = matrix.create_matrix(KineticEnergyIntegral(basis_set_array))
    print('\nKinetic Energy Matrix')
    print(t_matrix)
    v_matrix = matrix.create_matrix(NuclearAttractionIntegral(nuclei_array, basis_set_array))
    print('\nNuclear Potential Energy Matrix')
    print(v_matrix)

    print('\n*********************************************************************************************************')
    print('\nH_CORE AND TRANSFORMATION MATRIX\n')

    h_core_matrix = t_matrix + v_matrix
    print('\nH_CORE')
    print(h_core_matrix)

    s_matrix_eigenvalues, s_matrix_unitary = np.linalg.eig(s_matrix)
    x_canonical = s_matrix_unitary * np.diag(s_matrix_eigenvalues ** (-1/2))
    print('\nTRANSFORMATION MATRIX')
    print(x_canonical)

    print('\n*********************************************************************************************************')
    print('\nDENSITY MATRIX INITIAL GUESS\n')

    """
    Create a initial guess for the density matrix by turning off all two-electron interaction and solving for the
    orbital coefficients. The two-electron parts are then turned back on during the SCF procedure.
    """

    orthonormal_h_matrix = x_canonical.T * h_core_matrix * x_canonical

    eigenvalues,eigenvectors = np.linalg.eig(orthonormal_h_matrix)
    sort = eigenvalues.argsort()[::1]
    eigenvalues = eigenvalues[sort]
    eigenvectors = eigenvectors[:, sort]

    orbital_energy_matrix = np.diag(eigenvalues)
    print('\nORBITAL ENERGY EIGENVALUES')
    print(orbital_energy_matrix)

    orbital_coefficients = x_canonical * eigenvectors
    print('\nORBITAL COEFFICIENTS')
    print(orbital_coefficients)

    """
    The negative signs that numpy give for the orbital coefficients seems strange but it is because the sign of the
    orbitals and its wave-function can either have positive or negative values, the square of the wave-function, the
    electron density, will always end up being positive valued. The elements in the density matrix will made by
    multiplying two of the orbital coefficients together anyway
    """

    density_matrix = DensityMatrixElement(orbital_coefficients, electrons)
    p_matrix = matrix.create_matrix(density_matrix)
    print('\nDENSITY MATRIX')
    print(p_matrix)

    print('\n*********************************************************************************************************')
    print('\nBEGIN SCF PROCEDURE')
    total_energy = TotalEnergy()
    scf_procedure = SCFProcedure(h_core_matrix, x_canonical, matrix, total_energy, nuclear_repulsion_energy, basis_set_array, electrons)
    scf_procedure.begin_scf(p_matrix)

    print('\n*********************************************************************************************************')
    print('\nTime Taken: ' + str(time.clock() - start) + 's')
    print("\nWhat I cannot create I cannot understand - Richard Feynman\n")
