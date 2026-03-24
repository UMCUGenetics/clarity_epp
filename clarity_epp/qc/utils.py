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
