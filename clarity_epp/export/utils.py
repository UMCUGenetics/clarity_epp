"""Utility functions used for creating samplesheets."""
import re
import string


def sort_96_well_plate(wells):
    """Sort 96 well plate wells in vertical order.

    Arguments:
    wells -- unordered list of wells: ['A1', 'C1', 'E1', 'B1', 'D1']

    """
    order = plate96_wells()
    order = dict(zip(order, range(len(order))))

    wells = sorted(wells, key=lambda val: order[val])
    return wells


def reverse_complement(dna_sequence):
    """Return reverse complement DNA sequence."""
    complement = [{'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}[base] for base in dna_sequence]
    reverse_complement = reversed(complement)
    return ''.join(reverse_complement)


def sort_artifact_list(artifact):
    if '-' in artifact.id:
        return int(artifact.id.split('-')[1])
    else:
        return -1


def get_process_types(lims, process_types_names):
    """Get process types by partial name.

    If complete name is known use lims.get_process_types(displayname="complete name")
    """
    all_process_types = lims.get_process_types()
    process_types = []

    for process_type in all_process_types:
        for process_types_name in process_types_names:
            if process_types_name in process_type.name:
                process_types.append(process_type.name)

    return process_types


def get_well_index(well, one_based=False):
    """Return well index

    Arguments:
    well -- well str: 'A1'

    """
    wells = plate96_wells()

    if one_based:
        return wells.index(well) + 1
    else:
        return wells.index(well)


def get_sample_sequence_index(reagent_label):
    """Return sample sequence indices [index1, index2] from reagent label.
    expected reagent label pattern = "<index name> (index1-index2)" or "<index name> (index1)"
    """
    sample_index_search = re.search(r"\(([ACTGN-]+)\)$", reagent_label)
    sample_index = sample_index_search.group(1).split('-')

    return sample_index

def plate96_wells() -> list[str]:
    """
    Make a list of plate96 wells, [A1, B1, C1, D1, E1, F1, G1, H1, etc.].

    Returns:
        list[str]: a list of well names.
    """
    wells: list[str] = []
    for col in range(1, 13):
        wells.extend([f"{row}{col}" for row in string.ascii_uppercase[:8]])
    return wells

def nm_from_ng_ul(concentration_ng_ul: float, fragment_bp: float) -> float:
    """
    Calculate ng/µl to nM (with 660 g/mol/bp).
    Args:
        concentration_ng_ul: a float containing the concentration in ng/ul
        fragment_bp: a float containing the fragment length in bp

    Returns:
        float: the nM concentration
    """
    # nM = (ng/µl * 1e3 (pg/ng) / (660 g/mol/bp) / bp) * 1e3 (µl/L)
    return concentration_ng_ul * 1000.0 * (1 / 660.0) * (1 / fragment_bp) * 1000.0

def location_to_well(org_well: str) -> str:
    """
    Remove the colon (":"), e.g A:1 to A1

    Args:
        org_well: original well name containing a colon (":")

    Returns:
        str: the well name without the colon (":")
    """
    return "".join((org_well or "").split(":"))
