"""Utility functions."""
from datetime import datetime
import re

from genologics.entities import Workflow

import config


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


def transform_sample_name(value):
    """Transform legacy name to new sample name."""
    if '/' in value:
        sample_name = ''.join(value.split('/'))
        return sample_name
    else:
        return value


def stoftestcode_to_workflow(lims, stoftestcode):
    """Return workflow based on helix stoftestcode."""
    if stoftestcode in config.stoftestcode_workflow:
        return Workflow(lims, id=config.stoftestcode_workflow[stoftestcode])
    else:
        return None
