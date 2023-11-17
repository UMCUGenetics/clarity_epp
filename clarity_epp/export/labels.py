"""Export label functions."""

from genologics.entities import Process

from .. import get_mix_sample_barcode


def container(lims, process_id, output_file, description=''):
    """Generate container label file."""
    process = Process(lims, id=process_id)
    for index, container in enumerate(sorted(process.output_containers(), key=lambda container: container.id, reverse=True)):
        if description:
            if ',' in description:
                output_file.write('{description}\t{container}\r\n'.format(
                    description=description.split(',')[index],
                    container=container.name
                ))
            else:
                output_file.write('{description}\t{container}\r\n'.format(description=description, container=container.name))
        else:
            output_file.write('{container}\r\n'.format(container=container.name))


def container_sample(lims, process_id, output_file, description=''):
    """Generate container & artifact name label file."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        for artifact in container.placements.values():
            if description:
                output_file.write('{description}\t{sample}\t{container}\r\n'.format(
                    description=description,
                    container=container.name,
                    sample=artifact.name
                ))
            else:
                output_file.write('{sample}\t{container}\r\n'.format(container=container.name, sample=artifact.name))


def storage_location(lims, process_id, output_file):
    """Generate storage location label file."""
    process = Process(lims, id=process_id)

    # Write header
    output_file.write('Bakje\tpos\r\n')

    for artifact in process.analytes()[0]:
        for sample in artifact.samples:
            storage_location = sample.udf['Dx Opslaglocatie'].split()
            output_file.write('{tray}\t{pos}\r\n'.format(
                tray=storage_location[0][2:6],  # Select 4 digits from: CB[1-9][1-9][1-9][1-9]KK
                pos=storage_location[1]
            ))


def nunc_mix_sample(lims, process_id, output_file):
    """Generate (mix) sample nunc label file."""
    process = Process(lims, id=process_id)

    # Write empty header
    output_file.write('\r\n')

    for artifact in process.analytes()[0]:
        well = ''.join(artifact.location[1].split(':'))
        sample_mix = False
        if len(artifact.samples) > 1:
            sample_mix = True

        if sample_mix:
            barcode_name = get_mix_sample_barcode(artifact)
            output_file.write('{sample};;;;;{container}:{well};;1\r\n'.format(
                sample=barcode_name,
                container=artifact.container.name,
                well=well
            ))
        else:
            output_file.write('{sample};;;;;{container}:{well};;1\r\n'.format(
                sample=artifact.samples[0].udf['Dx Fractienummer'],
                container=artifact.container.name,
                well=well
            ))
