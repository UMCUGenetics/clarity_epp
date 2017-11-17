"""Label functions."""

from genologics.entities import Process

def container_label(lims, process_id, output_file):
    """Generates container list"""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        output_file.write('{container}\n'.format(container=container.name))
