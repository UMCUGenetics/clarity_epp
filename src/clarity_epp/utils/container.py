def get_96_well_plate() -> list[str]:
    """
    Return a list representing a 96 well plate in standard order.

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
