"""Artifact placement functions."""

from genologics.entities import Process


def set_sequence_name(lims, process_id):
    """Change artifact name to sequnece name."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        artifact.name = artifact.samples[0].name + 'SequenceName'  # TODO: change to real sequence name once available.
        artifact.put()
