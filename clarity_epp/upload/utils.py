"""Utility functions."""
from genologics.entities import Workflow


def char_to_bool(letter):
    """Transform character (J/N) to Bool."""
    if letter.upper() == 'J':
        return True
    elif letter.upper() == 'N':
        return False
    else:
        raise ValueError('Invalid character, only J or N allowed.')


def transform_sex(value):
    """Transform helix sex/geslacht value to lims sex/geslacht value."""
    if value.strip():
        if value.upper() == 'M':
            return 'Man'
        elif value.upper() == 'V':
            return 'Vrouw'
        elif value.upper() == 'O':
            return 'Onbekend'
        else:
            raise ValueError('Invalid sex character, only M, V or O allowed.')
    else:
        return value


def stofcode_to_workflow(lims, stofcode):
    """Return workflow based on helix stofcode."""
    if stofcode == 'NGS_008':
        return Workflow(lims, id='401')  # Dx Exoom HyperPlus v0.1
    else:
        return None
