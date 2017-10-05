"""Utility functions used for uploading samples."""
from genologics.entities import Workflow


def letter_to_bool(letter):
    """Transform letter (Y/N) to Bool."""
    if letter.upper() == 'J':
        return True
    elif letter.upper() == 'N':
        return False


def value_to_bool(value):
    """Transform value to Bool."""
    if len(value) != 0:
        return True
    elif len(value) == 0:
        return False


def stofcode_to_workflow(lims, stofcode):
    """Return workflow based on stofcode."""
    if stofcode == 'NGS_008':
        return Workflow(lims, id='351')  # Dx Exoom HyperPlus_manueel BBSS
    else:
        return Workflow(lims, id='352')  # Dx Aandachtspunten
