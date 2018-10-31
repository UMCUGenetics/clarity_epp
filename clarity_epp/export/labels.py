"""Export label functions."""

import re

from genologics.entities import Process


def container(lims, process_id, output_file, description):
    """Generate container label file."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        if description:
            output_file.write('{description} {container}\t{container}\r\n'.format(description=description, container=container.name))
        else:
            output_file.write('{container}\r\n'.format(container=container.name))


def container_sample(lims, process_id, output_file):
    """Generate container & artifact name label file."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        for artifact in container.placements.values():
            output_file.write('{container}\t{sample}\r\n'.format(container=container.name, sample=artifact.name))


def storage_location(lims, process_id, output_file):
    """Generate storage location label file."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        storage_location = artifact.samples[0].udf['Dx Opslaglocatie']
        m = re.search('\D+(\d+)\w+: (\d+)', storage_location)
        output_file.write('{sample}\t{storage_location}\t{tray}\t{tray_position}\n'.format(
            sample=artifact.samples[0].name,
            storage_location=storage_location,
            tray=m.group(1),
            tray_position=m.group(2)
        ))
