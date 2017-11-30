"""Utility functions."""
from genologics.entities import Workflow


def letter_to_bool(letter):
    """Transform letter (Y/N) to Bool."""
    if letter.upper() == 'J':
        return True
    elif letter.upper() == 'N':
        return False


def foetus_to_bool(value):
    """Transform helix foetus value to Bool."""
    if value == ' - 1':
        return True
    else:
        return False


def transform_sex(value):
    """Transform helix sex/geslacht value to lims sex/geslacht value."""
    if value.upper() == 'M':
        return 'Man'
    elif value.upper() == 'V':
        return 'Vrouw'
    elif value.upper() == 'O':
        return 'Onbekend'
    else:
        return value


def stofcode_to_workflow(lims, stofcode):
    """Return workflow based on helix stofcode."""
    if stofcode == 'NGS_008':
        return Workflow(lims, id='401')  # Dx Exoom HyperPlus v0.1
    else:
        return None
