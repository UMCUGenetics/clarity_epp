"""Utility functions used for creating samplesheets."""


def sort_96_well_plate(wells):
    """Sort 96 well plate wells in vertical order.

    Arguments:
    wells -- unordered list of wells: ['A1', 'C1', 'E1', 'B1', 'D1']

    """
    order = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1',
        'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
        'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5',
        'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7',
        'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9',
        'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11',
        'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]
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
    wells = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1',
        'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
        'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5',
        'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7',
        'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9',
        'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11',
        'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]

    if one_based:
        return wells.index(well) + 1
    else:
        return wells.index(well)
