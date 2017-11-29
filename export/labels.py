"""Export label functions."""

from genologics.entities import Process


def containers(lims, process_id, output_file):
    """Generate container label file."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        output_file.write('{container}\r\n'.format(container=container.name))
