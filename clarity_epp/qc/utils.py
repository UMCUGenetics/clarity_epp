"""Utility functions."""


def transform_sex_multiqc(value):
    """Transform multiqc sex value to lims sex value."""
    if value is not None and value.strip():
        if value.upper() == 'XX':
            return 'Vrouw'
        elif value.upper() == 'XY':
            return 'Man'
        else:
            return 'Onbekend'
    else:
        return 'Onbekend'

def is_missing(value):
    """Check if value is None or -1 (NA)

    Args:
        value (int | float | None):  Value to check.

    Returns:
        bool: True if the value is None of -1, False otherwise.
    """
    return value is None or value == -1