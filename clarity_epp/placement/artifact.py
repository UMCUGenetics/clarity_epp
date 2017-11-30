"""Artifact placement functions."""

from genologics.entities import Process

from .. import get_sequence_name


def set_sequence_name(lims, process_id):
    """Change artifact name to sequnece name."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        sample = artifact.samples[0]
        artifact.name = get_sequence_name(sample)
        artifact.put()
