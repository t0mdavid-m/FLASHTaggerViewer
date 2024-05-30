import streamlit as st
from pyopenms import Residue, AASequence, ModificationsDB


fixed_mod_cysteine = {'No modification': 0,
                      'Carbamidomethyl (+57)': 57.021464,
                      'Carboxymethyl (+58)': 58.005479,
                      'Xlink:Disulfide (-1 per C)': -1.007825,
                      }
fixed_mod_methionine = {'No modification': 0,
                        'L-methionine sulfoxide (+16)': 15.994915,
                        'L-methionine sulfone (+32)': 31.989829
                        }
H20 = 18.010564683
NH3 = 17.0265491015


def remove_ambigious(protein : AASequence):
    return AASequence.fromString(
        protein.toUniModString().replace('X', '').replace('x', '')
    )


# NOTE: cannot cache this function: cannot hash "OpenMS.AASequence"
def getFragmentMassesWithSeq(protein, res_type):
    protein_length = protein.size()
    prefix_mass_list = [.0] * protein_length
    suffix_mass_list = [.0] * protein_length

    # get type for fragments
    prefix_ion_type, suffix_ion_type = None, None
    if res_type == 'ax':
        prefix_ion_type = Residue.ResidueType.AIon
        suffix_ion_type = Residue.ResidueType.XIon
    elif res_type == 'by':
        prefix_ion_type = Residue.ResidueType.BIon
        suffix_ion_type = Residue.ResidueType.YIon
    elif res_type == 'cz':
        prefix_ion_type = Residue.ResidueType.CIon
        suffix_ion_type = Residue.ResidueType.ZIon

    # process prefix
    for aa_index in range(protein_length):
        prefix_mass = remove_ambigious(protein.getPrefix(aa_index+1)).getMonoWeight(prefix_ion_type, 0)  # + added_ptm_masses
        prefix_mass_list[aa_index] = prefix_mass

    # process suffix
    for aa_index in reversed(range(protein_length)):
        suffix_mass = remove_ambigious(protein.getSuffix(aa_index+1)).getMonoWeight(suffix_ion_type, 0)  # + added_ptm_masses
        suffix_mass_list[aa_index] = suffix_mass

    return prefix_mass_list, suffix_mass_list


# NOTE: cannot cache this function: cannot hash "OpenMS.AASequence"
def setFixedModification(protein):
    fixed_mod_site = []

    # fixed modification on cysteine
    if 'fixed_mod_cysteine' in st.session_state and st.session_state['fixed_mod_cysteine']:
        mod_mass = fixed_mod_cysteine[st.session_state['fixed_mod_cysteine']]
        for index, aa in enumerate(protein.toString()):
            if aa != 'C':
                continue
            # to remove warning, setModificationByDiffMonoMass was not used.
            mod = ModificationsDB().getBestModificationByDiffMonoMass(mod_mass, 0.001, 'C', 0)
            protein.setModification(index, mod)
        fixed_mod_site.append('C')

    # fixed modification on methionine
    if 'fixed_mod_methionine' in st.session_state and st.session_state['fixed_mod_methionine']:
        mod_mass = fixed_mod_methionine[st.session_state['fixed_mod_methionine']]
        for index, aa in enumerate(protein.toUnmodifiedString()):
            if aa != 'M':
                continue
                # to remove warning, setModificationByDiffMonoMass was not used.
            mod = ModificationsDB().getBestModificationByDiffMonoMass(mod_mass, 0.001, 'M', 0)
            protein.setModification(index, mod)
        fixed_mod_site.append('M')

    return protein, fixed_mod_site


#@st.cache_data
def getFragmentDataFromSeq(sequence, coverage=None, maxCoverage=None):
    protein = AASequence.fromString(sequence)
    protein, fixed_mods = setFixedModification(protein)  # handling fixed modifications

    # calculating proteoform mass from sequence
    protein_mass = remove_ambigious(protein).getMonoWeight()

    out_object = {'sequence': list(sequence),
                  'theoretical_mass': protein_mass, 
                  'fixed_modifications': fixed_mods}
    if coverage is not None:
        out_object['coverage'] = list(coverage)
    if maxCoverage is not None:
        out_object['maxCoverage'] = maxCoverage

    # per ion type, calculate the possible fragment masses and save them in dictionary
    for ion_type in ['ax', 'by', 'cz']:
        # calculate fragment ion masses
        prefix_ions, suffix_ions = getFragmentMassesWithSeq(protein, ion_type)
        out_object['fragment_masses_%s' % ion_type[0]] = prefix_ions
        out_object['fragment_masses_%s' % ion_type[1]] = suffix_ions
    return out_object

# Define amino acid masses with high resolution
aa_masses = {
    'A': 71.037114,
    'R': 156.101111,
    'N': 114.042927,
    'D': 115.026943,
    'C': 103.009185,
    'E': 129.042593,
    'Q': 128.058578,
    'G': 57.021464,
    'H': 137.058912,
    'I': 113.084064,
    'L': 113.084064,
    'K': 128.094963,
    'M': 131.040485,
    'F': 147.068414,
    'P': 97.052764,
    'S': 87.032028,
    'T': 101.047679,
    'W': 186.079313,
    'Y': 163.063329,
    'V': 99.068414,
    'X' : 0
}

def isMatchWithTolerance(A, t, s):
    """
    Check if there is a value in sorted list A that matches t within a given ppm tolerance s.

    Parameters:
    A (list of float): Sorted list of values.
    t (float): The target value to match.
    s (float): The tolerance in parts per million (ppm).

    Returns:
    bool: True if there is a match within the tolerance, False otherwise.
    """
    # Convert the tolerance from ppm to an absolute value
    tolerance = t * s / 1e6

    # Binary search approach for efficiency due to the sorted nature of A
    left, right = 0, len(A) - 1

    while left <= right:
        mid = (left + right) // 2
        if abs(A[mid] - t) <= tolerance:
            return True
        elif A[mid] < t:
            left = mid + 1
        else:
            right = mid - 1

    return False


def getInternalFragmentMassesWithSeq(sequence, res_type):
    shift = -H20 if res_type == 'by' or res_type == 'cz' else (-H20-NH3 if res_type == 'bz' else -H20+NH3)
    masses = []
    start_indices = []
    end_indices = []
    # protein('sequence', protein.toString())

    protein = AASequence.fromString(sequence)#tmp code
    byp, bys = getFragmentMassesWithSeq(protein, 'by') #tmp code
    czp, czs = getFragmentMassesWithSeq(protein, 'cz') #tmp code

    termianl_masses = byp + bys + czp + czs#tmp code
    termianl_masses.sort()#tmp code

    for i, s in enumerate(sequence):
        if i == 0:
            continue
        if i == len(sequence)-1:
            break
        mass = 0.0
        for j, t in enumerate(sequence):
            if j >= i:
                mass = mass + aa_masses[sequence[j]]
            if j < i+5-1:
                continue

            if isMatchWithTolerance(termianl_masses, mass, 10.0): #tmp code
                continue #tmp code

            masses.append(mass + 18.010564683 + shift)
            start_indices.append(i)
            end_indices.append(j+1)

    return masses, start_indices, end_indices


#@st.cache_data
def getInternalFragmentDataFromSeq(sequence):
    # TODO: fixed modification
    # protein = AASequence.fromString(sequence)
    # protein, fixed_mods = setFixedModification(protein)  # handling fixed modifications

    out_object = {}  # sequence information is from "sequence_data"
    for ion_type in ['by', 'bz', 'cy']:  # by cz are the same.
        ions, start_indices, end_indices = getInternalFragmentMassesWithSeq(sequence, ion_type)
        out_object['fragment_masses_%s' % ion_type] = ions
        out_object['start_indices_%s' % ion_type] = start_indices
        out_object['end_indices_%s' % ion_type] = end_indices

    return out_object
