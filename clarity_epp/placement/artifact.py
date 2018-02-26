"""Artifact placement functions."""

from genologics.entities import Process

from .. import get_sequence_name
import config


def set_sequence_name(lims, process_id):
    """Change artifact name to sequnece name."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        sample = artifact.samples[0]
        artifact.name = get_sequence_name(sample)
        artifact.put()


def set_runid_name(lims, process_id):
    """Change artifact name to run id."""
    process = Process(lims, id=process_id)
    analyte = process.analytes()[0][0]
    input_artifact = process.all_inputs()[0]

    # Find sequencing process
    # Assume one sequence process per input artifact
    for sequence_process_type in config.sequence_process_types:
        sequence_process = lims.get_processes(type=sequence_process_type, inputartifactlimsid=input_artifact.id)[0]
        if sequence_process:
            analyte.name = sequence_process.udf['Run ID']
            analyte.put()
