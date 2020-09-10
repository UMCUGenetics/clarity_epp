"""Export label functions."""

from genologics.entities import Process


def container(lims, process_id, output_file, description=''):
    """Generate container label file."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        if description:
            output_file.write('{description}\t{container}\r\n'.format(description=description, container=container.name))
        else:
            output_file.write('{container}\r\n'.format(container=container.name))


def container_sample(lims, process_id, output_file, description=''):
    """Generate container & artifact name label file."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        for artifact in container.placements.values():
            if description:
                output_file.write('{description}\t{sample}\t{container}\r\n'.format(description=description, container=container.name, sample=artifact.name))
            else:
                output_file.write('{sample}\t{container}\r\n'.format(container=container.name, sample=artifact.name))


def storage_location(lims, process_id, output_file):
    """Generate storage location label file."""
    process = Process(lims, id=process_id)
    for artifact in process.analytes()[0]:
        storage_location = artifact.samples[0].udf['Dx Opslaglocatie']
        output_file.write('{sample}\t{storage_location}\t{birth_date}\n'.format(
            sample=artifact.samples[0].name,
            storage_location=storage_location,
            birth_date=artifact.samples[0].udf['Dx Geboortejaar']
        ))
