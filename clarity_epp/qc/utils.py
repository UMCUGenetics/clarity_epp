"""Utility functions."""


def transform_sex_multiqc(value):
    """Transform multiqc sex value to lims sex value."""
    if value.strip():
        if value.upper() == 'XX':
            return 'Vrouw'
        elif value.upper() == 'XY':
            return 'Man'
        else:
            return value
    else:
        return value
