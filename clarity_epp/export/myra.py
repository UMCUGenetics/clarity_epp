"""Myra export functions."""

from genologics.entities import Process


def samplesheet_to_callisto(lims, process_id, output_file):
    """Generate Myra samplesheet

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): Myra samplesheet file path.
    """
    process = Process(lims, id=process_id)
    output_file.write('sample_ID,input_ID,well_input_ID,output_ID,volume\n')

    row_number = {"A": "1", "D": "2", "G": "3"}
    wells = {
        "8 well strip Callisto":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8'],
        "16 Wells Strip Callisto":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
         'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8'],
        "24 Wells Strip Callisto":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
         'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8',
         'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8']
    }

    output_data = {}

    for output_artifact in process.analytes()[0]:
        input_artifact = output_artifact.input_artifact_list()[0]
        output_id = output_artifact.container.id
        if output_id not in output_data:
            output_data[output_id] = {"type": output_artifact.container.type.name}
        output_well = ''.join(output_artifact.location[1].split(':'))
        output_row = row_number[output_artifact.location[1][0]]
        label_id = '{output}_{number}'.format(output=output_id, number=output_row)
        line = '{sample},{input},{input_well},{output},{volume}'.format(
            sample=output_artifact.name,
            input=input_artifact.container.id,
            input_well=''.join(input_artifact.location[1].split(':')),
            output=label_id,
            volume=process.udf['Dx pipetteervolume (ul)']
        )
        output_data[output_id][output_well] = line

    for output_id in output_data:
        for well in wells[output_data[output_id]["type"]]:
            if well in output_data[output_id]:
                output_file.write('{line}\n'.format(line=output_data[output_id][well]))
            else:
                output_file.write('LEEG,,,{output},{well},,\n'.format(output=output_id, well=well))


def samplesheet_from_callisto(lims, process_id, output_file):
    """Generate Myra samplesheet

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): Myra samplesheet file path.
    """
    process = Process(lims, id=process_id)
    output_file.write('sample_ID,input_ID,well_input_ID,output_ID,volume\n')

    row_number = {"A": "1", "D": "2", "G": "3"}
    wells = {
        "8 well strip Callisto":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8'],
        "16 Wells Strip Callisto":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
         'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8'],
        "24 Wells Strip Callisto":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
         'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8',
         'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8']
    }

    output_data = {}

    for output_artifact in process.analytes()[0]:
        input_artifact = output_artifact.input_artifact_list()[0]
        input_id = input_artifact.container.id
        if input_id not in output_data:
            output_data[input_id] = {"type": input_artifact.container.type.name}
        input_well = ''.join(input_artifact.location[1].split(':'))
        input_row = row_number[input_artifact.location[1][0]]
        label_id = '{output}_{number}'.format(output=input_id, number=input_row)
        line = '{sample},{input},{input_well},{output},{volume}'.format(
            sample=output_artifact.name,
            input=input_artifact.container.id,
            input_well=''.join(input_artifact.location[1].split(':')),
            output=label_id,
            volume=process.udf['Dx pipetteervolume (ul)']
        )
        output_data[input_id][input_well] = line

    for input_id in output_data:
        for well in wells[output_data[input_id]["type"]]:
            if well in output_data[input_id]:
                output_file.write('{line}\n'.format(line=output_data[input_id][well]))
            else:
                output_file.write('LEEG,,,{output},{well},,\n'.format(output=input_id, well=well))
