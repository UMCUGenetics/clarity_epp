"""Utilities to manage container layouts.

A container in the context of Clarity LIMS is defined as a physical vessel used to hold and identify biological samples or
their derivatives during laboratory processing. In Clarity LIMS, a container is represented by a system resource that records
its identity, type and the location of its contents. Depending on the container, samples may occupy a single position or
multiple positions, such as wells in a microplate. Clarity LIMS tracks sample placement in containers throughout the workflow,
allowing samples and their processing history to be associated with their physical locations.
"""


def get_96_well_plate() -> list[str]:
    """Return a list representing a 96 well plate in standard order.

    Returns:
        List of well positions from A1 to H12.
    """
    wells = [f"{row}{col}" for col in range(1, 13) for row in "ABCDEFGH"]
    return wells


def sort_96_well_plate(wells: list[str]) -> list[str]:
    """Sort 96 well plate wells in vertical order.

    Args:
        wells: List of well positions.

    Returns:
        Sorted list of well positions.
    """
    order = get_96_well_plate()
    order = dict(zip(order, range(len(order))))

    wells = sorted(wells, key=lambda val: order[val])
    return wells
