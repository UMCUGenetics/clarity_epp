"""Utility functions."""



def transform_sex_multiqc(value):
    """Transform multiqc sex missing values to 'Onbekend' and keep valid values."""
    if value is None or not value.strip():
        return 'Onbekend'
    value = value.strip()
    if value in ('Man', 'Vrouw'):
        return value
    return 'Onbekend'


def is_missing(value):
    """Check if value is None or -1 (NA)

    Args:
        value (int | float | None):  Value to check.

    Returns:
        bool: True if the value is None of -1, False otherwise.
    """
    return value is None or value == -1