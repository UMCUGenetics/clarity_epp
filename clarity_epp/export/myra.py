"""Myra export functions."""
import string

from genologics.entities import Process


def samplesheet_callisto(lims, process_id, output_file):
    """Generate Myra samplesheet for step with Callisto strips as input container or output container

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): Myra samplesheet file path.
    """
    process = Process(lims, id=process_id)
    output_file.write('sample_ID,input_ID,well_input_ID,output_ID,well_output_ID,volume\n')

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
        input_well = ''.join(input_artifact.location[1].split(':'))
        output_id = output_artifact.container.id
        output_well = ''.join(output_artifact.location[1].split(':'))
        label_id = ''

        # Callisto strip is input container
        if "Callisto" in input_artifact.container.type.name:
            strip_id = input_id
            type = input_artifact.container.type.name
            strip_well = input_well
        # Callisto strip is output container
        elif "Callisto" in output_artifact.container.type.name:
            strip_id = output_id
            type = output_artifact.container.type.name
            strip_well = output_well
            row = row_number[output_artifact.location[1][0]]
            label_id = '{strip}_{number}'.format(strip=strip_id, number=row)

        if strip_id not in output_data:
            output_data[strip_id] = {"type": type}

        # Callisto strip is output container
        if label_id:
            output = label_id
        # Callisto strip is input container
        else:
            output = output_id

        line = '{sample},{input},{input_well},{output},{output_well},{volume}'.format(
            sample=output_artifact.name,
            input=input_artifact.container.id,
            input_well=''.join(input_artifact.location[1].split(':')),
            output=output,
            output_well=output_well,
            volume=process.udf['Dx pipetteervolume (ul)']
        )
        output_data[strip_id][strip_well] = line

    # Write output for every well of Callisto strip (Callisto strip is input container and Callisto strip is output container)
    for strip_id in output_data:
        for well in wells[output_data[strip_id]["type"]]:
            if well in output_data[strip_id]:
                output_file.write('{line}\n'.format(line=output_data[strip_id][well]))
            else:
                # Callisto strip well is empty
                output_file.write('LEEG,,,,\n')


def samplesheet_dilute(lims, process_id, output_file):
    """Create Myra samplesheet for diluting samples.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): Myra samplesheet file path.
    """
    output_file.write(
        'Monsternummer;Plate_Id_input;Well;Plate_Id_output;Pipetteervolume DNA (ul);Pipetteervolume H2O (ul)\n'
    )
    process = Process(lims, id=process_id)

    output = {}  # save output data to dict, to be able to sort on well.
    nM_pool = process.udf['Dx Pool verdunning (nM)']
    output_ul = process.udf['Eindvolume (ul)']

    # Get input and output plate id from 1 sample, input plate is the same for all samples.
    input_artifacts = process.all_inputs()
    plate_id_artifact = input_artifacts[0]
    plate_id_input = plate_id_artifact.location[0].name
    plate_id_output = process.outputs_per_input(plate_id_artifact.id, Analyte=True)[0].location[0].name

    for input_artifact in input_artifacts:
        # Get QC stats
        size = float(input_artifact.udf['Dx Fragmentlengte (bp)'])
        concentration = float(input_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        # Calculate dilution
        nM_dna = (concentration * 1000 * (1/660.0) * (1/size)) * 1000
        ul_sample = (nM_pool/nM_dna) * output_ul
        ul_water = output_ul - ul_sample

        # Store output lines by well
        well = ''.join(input_artifact.location[1].split(':'))
        output[well] = '{name};{plate_id_input};{well};{plate_id_output};{volume_dna:.1f};{volume_water:.1f}\n'.format(
            name=input_artifact.name,
            plate_id_input=plate_id_input,
            well=well,
            plate_id_output=plate_id_output,
            volume_dna=ul_sample,
            volume_water=ul_water
        )

    wells = []
    for col in range(1, 13):
        wells.extend(['{}{}'.format(row, str(col)) for row in string.ascii_uppercase[:8]])

    for well in wells:
        if well in output:
            output_file.write(output[well])
        else:
            output_file.write('Leeg;{plate_id_input};{well};{plate_id_output};0;0\n'.format(
                plate_id_input=plate_id_input,
                well=well,
                plate_id_output=plate_id_output,
            ))
