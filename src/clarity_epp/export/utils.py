"""Utility functions used for creating samplesheets."""

import re


def get_96_well_plate() -> list[str]:
    """
    Return a list representing a 96 well plate in standard order.

    Returns:
        list[str]: List of well positions from A1 to H12.
    """
    wells = [f"{row}{col}" for col in range(1, 13) for row in "ABCDEFGH"]
    return wells


def sort_96_well_plate(wells: list[str]) -> list[str]:
    """Sort 96 well plate wells in vertical order.

    Args:
        wells (list[str]): List of well positions.
    Returns:
        list[str]: Sorted list of well positions.
    """
    order = get_96_well_plate()
    order = dict(zip(order, range(len(order))))

    wells = sorted(wells, key=lambda val: order[val])
    return wells


def reverse_complement(dna_sequence):
    """Return reverse complement DNA sequence."""
    complement = [{"A": "T", "C": "G", "G": "C", "T": "A"}[base] for base in dna_sequence]
    reverse_complement = reversed(complement)
    return "".join(reverse_complement)


def sort_artifact_list(artifact):
    if "-" in artifact.id:
        return int(artifact.id.split("-")[1])
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
    wells = get_96_well_plate()

    if one_based:
        return wells.index(well) + 1
    else:
        return wells.index(well)


def get_sample_sequence_index(reagent_label):
    """Return sample sequence indices [index1, index2] from reagent label.
    expected reagent label pattern = "<index name> (index1-index2)" or "<index name> (index1)"
    """
    sample_index_search = re.search(r"\(([ACTGN-]+)\)$", reagent_label)
    sample_index = sample_index_search.group(1).split("-")

    return sample_index
