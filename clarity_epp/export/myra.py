"""Myra export functions."""
import string
import sys

from genologics.entities import Process

from clarity_epp.export.utils import (
    create_samplesheet, extract_well_from_reagent_label, get_input_containers, get_process_types,
    get_qc_values_parent_process_artifact, sort_dict_by_nested_well_location
)
from clarity_epp.placement.barcode import check_plate_id_with_used_reagent_labels


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
         'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8'],
        "24 Wells Strip Callisto barcoded":
        ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
         'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
         'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8']
    }

    output_data = {}

    for output_artifact in process.analytes()[0]:
        input_artifact = output_artifact.input_artifact_list()[0]
        input_name = input_artifact.container.name
        input_well = input_artifact.location[1].replace(':', '')
        output_name = output_artifact.container.name
        output_well = output_artifact.location[1].replace(':', '')
        label_id = ''

        # Callisto strip is input container
        if "Callisto" in input_artifact.container.type.name:
            strip_id = input_name
            type = input_artifact.container.type.name
            strip_well = input_well
        # Callisto strip is output container
        elif "Callisto" in output_artifact.container.type.name:
            strip_id = output_name
            type = output_artifact.container.type.name
            strip_well = output_well
            if "barcoded" not in output_artifact.container.type.name:
                row = row_number[output_artifact.location[1][0]]
                label_id = '{strip}_{number}'.format(strip=strip_id, number=row)

        if strip_id not in output_data:
            output_data[strip_id] = {"type": type}

        # Callisto strip is output container
        if label_id:
            output = label_id
        # Callisto strip is input container
        else:
            output = output_name

        line = '{sample},{input},{input_well},{output},{output_well},{volume}'.format(
            sample=output_artifact.name,
            input=input_artifact.container.name,
            input_well=input_well,
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
        well = input_artifact.location[1].replace(':', '')
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


def get_info_for_samplesheet_barcode(process):
    """Collects information for the Myra samplesheet barcode plate from the process and
    returns a dictionary containing this information organised by analytes.

    Args:
        process (object): Lims Process object

    Returns:
        dict: Dictionary containing the information for the samplesheet in a nested dictionary per analyte
    """
    analytes = process.analytes()[0]
    output = process.udf["Index strip barcode"]
    info_dictionary = {}
    for analyte in analytes:
        label_location = extract_well_from_reagent_label(analyte.reagent_labels[0])
        info_dictionary[analyte.name] = {
            "reagent": analyte.reagent_labels[0],
            "input": process.udf['Twist barcode plaat ID'],
            "well_input": label_location,
            "output": output,
            "well_output": "".join(analyte.location[1].split(":")),
        }
    return info_dictionary


def generate_samplesheet_barcode_plate(process):
    """Generates a Myra samplesheet for pipetting from barcode plate.

    Args:
        process (object): Lims Process object

    Returns:
        str: Myra samplesheet
    """
    info_dictionary = get_info_for_samplesheet_barcode(process)
    sorted_info_dictionary = sort_dict_by_nested_well_location(info_dictionary, "well_input")
    samplesheet_content = {"samples": sorted_info_dictionary}
    samplesheet = create_samplesheet("Samplesheet_Myra_Barcode.csv", samplesheet_content)
    return samplesheet


def check_plate_id_and_generate_samplesheet_barcode(lims, process_id, output_file):
    """Performs an index plate ID check and generates a samplesheet only when check is ok.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): File path for samplesheet
    """
    process = Process(lims, id=process_id)
    check_plate_id_with_used_reagent_labels(lims, process)
    # If check_plate_id_with_used_reagent_labels did not exit with a wrong plate message samplesheet will be generated
    samplesheet = generate_samplesheet_barcode_plate(process)
    output_file.write(samplesheet)


def get_info_for_samplesheet_placement_callisto(process, input_container):
    """Collects information for the Myra samplesheet placement Callisto from the given process input container and
    returns a dictionary containing this information organised by analytes.

    Args:
        process (object): Lims Process object
        input_container (str): Input container name

    Returns:
        dict: Dictionary containing the information for the samplesheet in a nested dictionary per analyte
    """
    analytes = process.analytes()[0]
    info_dictionary = {}

    for analyte in analytes:
        input_artifact = analyte.input_artifact_list()[0]
        if input_artifact.container.name == input_container:
            info_dictionary[analyte.name] = {
                "sample": analyte.name,
                "input": input_container,
                "well_input": input_artifact.location[1].replace(':', ''),
                "output": analyte.container.name,
                "well_output": analyte.location[1].replace(':', ''),
                "volume": process.udf['Dx pipetteervolume (ul)']
            }
    return info_dictionary


def generate_samplesheet_callisto_strip(process, input_container):
    """Generates a Myra samplesheet for pipetting from Callisto strip.

    Args:
        process (object): Lims Process object
        input_container (str): Input container name

    Returns:
        str: Myra Placement Callisto samplesheet
    """
    info_dictionary = get_info_for_samplesheet_placement_callisto(process, input_container)
    sorted_info_dictionary = sort_dict_by_nested_well_location(
        info_dictionary, "well_input", "24_well_barcoded_callisto_strip"
    )
    samplesheet_content = {"samples": sorted_info_dictionary}
    samplesheet = create_samplesheet("Samplesheet_Myra_Placement_Callisto.csv", samplesheet_content)
    return samplesheet


def get_input_containers_and_generate_samplesheet_callisto_strip(lims, process_id, output_files):
    """Gets all input_containers and generates a Callisto strip samplesheet per input container.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_files (list): List of file paths for samplesheets
    """
    process = Process(lims, id=process_id)
    input_containers = get_input_containers(process)

    number_of_inputs = len(input_containers)
    samplesheet_1 = generate_samplesheet_callisto_strip(process, input_containers[0])
    if number_of_inputs > 1:
        samplesheet_2 = generate_samplesheet_callisto_strip(process, input_containers[1])
    else:
        samplesheet_2 = "geen 2e input container"
    if number_of_inputs > 2:
        samplesheet_3 = generate_samplesheet_callisto_strip(process, input_containers[2])
    else:
        samplesheet_3 = "geen 3e input container"
    output_files[0].write(samplesheet_1)
    output_files[1].write(samplesheet_2)
    output_files[2].write(samplesheet_3)


def calculate_volumes_nM_diluting(nM_pool, ul_sample, size, concentration):
    """Calculates volume water for nM diluting given Analyte.

    Args:
        process (object): Lims Process object
        analyte (object): Lims Analyte object
        nM_pool (int): nM dilute value
        ul_sample (int): Sample volume

    Returns:
        float: Volume water for pipetting
    """
    nM_dna = (concentration * 1000 * (1/660.0) * (1/size)) * 1000
    output_ul = (nM_dna/nM_pool) * ul_sample
    ul_water = output_ul - ul_sample
    return ul_water


def get_info_for_samplesheet_dilute(process, input_container):
    """Collects information for the Myra samplesheet dilute from the given process input container and
    returns a dictionary containing this information organised by analytes.

    Args:
        process (object): Lims Process object
        input_container (str): Input container name

    Returns:
        dict: Dictionary containing the information for the samplesheet in a nested dictionary per analyte
    """
    analytes = process.analytes()[0]
    info_dictionary = {}
    nM_pool = process.udf['Dx Pool verdunning (nM)']
    volume_sample = process.udf['Sample volume (ul)']

    for analyte in analytes:
        input_artifact = analyte.input_artifact_list()[0]
        size, concentration = get_qc_values_parent_process_artifact(input_artifact)
        volume_water = calculate_volumes_nM_diluting(nM_pool, volume_sample, size, concentration)
        if input_artifact.container.name == input_container:
            info_dictionary[analyte.name] = {
                "sample": analyte.name,
                "input": input_container,
                "well_input": input_artifact.location[1].replace(':', ''),
                "output": analyte.container.name,
                "well_output": analyte.location[1].replace(':', ''),
                "volume_sample": f"{volume_sample:.1f}",
                "volume_water": f"{volume_water:.1f}"
            }
    return info_dictionary


def generate_samplesheet_dilute(process, input_containers):
    """Generates a Myra samplesheet for nM diluting.

    Args:
        process (object): Lims Process object
        input_containers (list): List of input container names

    Returns:
        str: Myra Dilute samplesheet
    """
    info_dictionary = {}
    for input_container in input_containers:
        info_input_dictionary = get_info_for_samplesheet_dilute(process, input_container)
        info_dictionary.update(info_input_dictionary)

    sorted_info_dictionary = sort_dict_by_nested_well_location(info_dictionary, "well_output", "96_well_plate")
    samplesheet_content = {"samples": sorted_info_dictionary}
    samplesheet = create_samplesheet("Samplesheet_Myra_Dilute.csv", samplesheet_content)
    return samplesheet


def get_input_containers_and_generate_samplesheet_dilute(lims, process_id, output_file):
    """Gets all input_containers and generates a dilute samplesheet.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): File path for samplesheet
    """
    process = Process(lims, id=process_id)
    input_containers = get_input_containers(process)
    samplesheet = generate_samplesheet_dilute(process, input_containers)
    output_file.write(samplesheet)


def check_for_missing_samples_in_file(process, cluster_dict):
    """Checks if all samples in process are in cluster_dict, exiting with message if not, else returning
    list with sample names (without _extension) in process

    Args:
        process (object): Lims Process object
        cluster_dict (dict): Dictionary containing per sample: 'clusters' (number of clusters) and 'project'

    Returns:
        list: List of sample names (without _extension) in process
    """
    process_samples = []
    for analyte in process.analytes()[0]:
        sample_name = analyte.name.split('_')[0]
        process_samples.append(sample_name)
        try:
            cluster_dict[sample_name]
        except (KeyError):
            message = (f'LP sample {analyte.name.split("_")[0]} niet aanwezig in het geuploade QC stats LowPass bestand')
            sys.exit(message)
    return process_samples


def check_for_missing_samples_in_process(cluster_dict, process_samples):
    """Checks if all samples in cluster_dict are in process_samples, adding any samples that are not to the returning
    missing_samples list, also removing these samples from cluster_dict and returning this updated dictionary

    Args:
        cluster_dict (dict): Dictionary containing per sample: 'clusters' (number of clusters) and 'project'
        process_samples (list): List of sample names (without _extension) in process

    Returns:
        tuple[list,dict]:
        List with missing sample names &
        Updated dictionary, missing samples removed
    """
    missing_samples = []
    for sample in cluster_dict:
        if sample not in process_samples:
            missing_samples.append(sample)

    for missing_sample in missing_samples:
        cluster_dict.pop(missing_sample)

    return missing_samples, cluster_dict


def get_LP_QC_stats(lims, process):
    """Gets number of clusters for LPsrWGS (project) samples from uploaded QC stats LowPass file and checks samples in
    file with samples in process, exiting with message if error in parsing file, else returning dictionary and list

    Args:
        lims (object): Lims connection
        process (object): Lims Process object

    Returns:
        tuple[dict,list]:
        Dictionary containing per sample: 'clusters' (number of clusters) and 'project' &
        List containing samplenames of samples present in QC stats LowPass file, but not in process analytes
    """
    cluster_dict = {}
    for output in process.all_outputs(unique=True):
        if output.name == 'QC stats LowPass':
            QC_stats_file_id = output.files[0].id
            QC_stats_file = lims.get_file_contents(QC_stats_file_id).data.decode('utf-8').rstrip().split('\n')
            for line in QC_stats_file:
                if line.startswith('Sample'):
                    header = line.split('\t')

    for line_index, line in enumerate(QC_stats_file):
        data = line.rstrip().split('\t')
        try:
            if ' - L' not in data[header.index('Sample')]:
                if 'LPsrWGS' in data[header.index('Project')]:
                    cluster_dict[data[header.index('Sample')].split(' (L')[0].split('_LPsrWGS')[0]] = {
                        'clusters': float(data[header.index('Clusters')]),
                        'project': data[header.index('Project')]
                    }
        except (IndexError, ValueError):
            message = (f'Error parsing file: line {line_index}')
            sys.exit(message)

    process_samples = check_for_missing_samples_in_file(process, cluster_dict)
    missing_samples, cluster_dict = check_for_missing_samples_in_process(cluster_dict, process_samples)

    return cluster_dict, missing_samples


def calculate_performances(cluster_dict, excluded_samples):
    """Calculates performance per sample based on number of clusters and updates cluster_dict with calculated performance

    Args:
        cluster_dict (dict): Dictionary containing per sample: 'clusters' (number of clusters) and 'project'
        excluded_samples (list): List containing all excluded analytes (udf 'Dx Geëxcludeerd LP' = True) in process

    Returns:
        dict: Updated dictionary cluster_dict ('performance' per sample added)
    """
    for artifact in excluded_samples:
        cluster_dict[artifact.name.split('_')[0]]['excluded'] = True

    nr_samples = 0
    total_clusters = 0.0
    for sample in cluster_dict:
        if 'excluded' not in cluster_dict[sample]:
            nr_samples += 1
            total_clusters += cluster_dict[sample]['clusters']

    average_clusters = total_clusters / nr_samples

    for sample in cluster_dict:
        if 'excluded' not in cluster_dict[sample]:
            sample_performance = cluster_dict[sample]['clusters'] / average_clusters
            cluster_dict[sample]['performance'] = sample_performance

    return cluster_dict


def calculate_volumes_nM_rediluting(nM_pool, ul_sample, size, concentration, performance):
    """Calculates volume water for nM rediluting given Analyte.

    Args:
        nM_pool (int): nM dilute value
        ul_sample (int): Sample volume
        size (float): size (fragmentlengte)
        concentration (float): concentration
        performance (float): calculated performance based on # clusters

    Returns:
        float: Volume water for pipetting
    """
    nM_dna = (concentration * 1000 * (1/660.0) * (1/size)) * 1000
    nM_sample_corrected = nM_pool * (1/performance)
    output_ul = (nM_dna/nM_sample_corrected) * ul_sample
    ul_water = output_ul - ul_sample
    return ul_water


def get_excluded_samples(process):
    """Checks every analyte in process and adds analyte to list if udf 'Dx Geëxcludeerd LP' value  == True

    Args:
        process (object): Lims Process object

    Returns:
        list: List containing excluded analytes (udf 'Dx Geëxcludeerd LP' == True)
    """
    excluded_samples = []
    analytes = process.analytes()[0]
    for analyte in analytes:
        if 'Dx Geëxcludeerd LP' in analyte.udf and analyte.udf['Dx Geëxcludeerd LP']:
            excluded_samples.append(analyte)
    return excluded_samples


def get_info_from_LP_process(lims, lowpass_processes, analyte):
    """Gets calculation information from udfs in LowPass process.

    Args:
        lims (object): Lims connection
        lowpass_processes (list): List of LowPass processtypes (Dx nM verdunning Myra LP)
        analyte (object): Artifact object from LowPass parent process (processtype: Dx sample duplicate)

    Returns:
        tuple[float,float]:
        nM dilution factor &
        Volume sample (ul)
    """
    lowpass_process = lims.get_processes(type=lowpass_processes, inputartifactlimsid=analyte.id)[0]
    nM_pool = float(lowpass_process.udf['Dx Pool verdunning (nM)'])
    volume_sample = float(lowpass_process.udf['Sample volume (ul)'])
    return nM_pool, volume_sample


def check_excluding_sample(dx_analyte, volume_water, performances_dict, new_samples_excluded):
    """Checks if sample needs to be excluded (based on volume_water);
    sample excluded: sets udf 'Dx Geëxcludeerd LP' and new_samples_excluded to True,
    sample not excluded: adds volume_water to performances_dict

    Args:
        dx_analyte (object): Artifact object
        volume_water (float): Calculated volume water
        performances_dict (dict): Dictionary containing 'performance' per sample
        new_samples_excluded (bool): Boolean

    Returns:
        tuple[dict,bool]:
        Supplied dictionary (performances_dict) updated with 'volume_water' per sample if sample is not excluded &
        Boolean (set to True if sample is excluded)
    """
    if volume_water < 0 or volume_water > 180:
        dx_analyte.udf['Dx Geëxcludeerd LP'] = True
        dx_analyte.put()
        new_samples_excluded = True
    else:
        performances_dict[dx_analyte.name.split('_')[0]]['volume_water'] = volume_water
    return performances_dict, new_samples_excluded


def fill_info_dictionary(dx_analytes, input_container, volumes_dict):
    """Fills a new dictionary with all the necessary info for the samplesheet

    Args:
        dx_analytes (list): List of Artifact objects
        input_container (str): Name of input container
        volumes_dict (dict): Dictionary containing 'volume_sample' and 'volume_water' per sample

    Returns:
        dict: Dictionary filled with info for filling samplesheet
    """
    info_dictionary = {}
    for dx_analyte in dx_analytes:
        input_artifact = dx_analyte.input_artifact_list()[0]
        if input_artifact.container.name == input_container:
            sample_name = dx_analyte.name.split('_')[0]
            if 'excluded' not in volumes_dict[sample_name] or not volumes_dict[sample_name]['excluded']:
                info_dictionary[dx_analyte.name] = {
                    "sample": dx_analyte.name,
                    "input": input_artifact.container.name,
                    "well_input": input_artifact.location[1].replace(':', ''),
                    "output": dx_analyte.container.name,
                    "well_output": dx_analyte.location[1].replace(':', ''),
                    "volume_sample": f"{volumes_dict[sample_name]['volume_sample']:.1f}",
                    "volume_water": f"{volumes_dict[sample_name]['volume_water']:.1f}"
                }
    return info_dictionary


def get_info_for_samplesheet_redilute(lims, process, input_container):
    """Collects information for the Myra samplesheet redilute from the given process input container and
    returns a dictionary containing this information organised by analytes and a list with missing samples

    Args:
        lims (object): Lims connection
        process (object): Lims Process object
        input_container (str): Input container name

    Returns:
        tuple[dict,list]:
        Dictionary containing the information for the samplesheet in a nested dictionary per analyte &
        List containing samplenames of samples present in QC stats LowPass file, but not in process analytes
    """
    cluster_dict, missing_samples = get_LP_QC_stats(lims, process)
    lowpass_processes = get_process_types(lims, ["Dx nM verdunning Myra LP"])

    new_samples_excluded = True
    while new_samples_excluded:
        new_samples_excluded = False
        excluded_samples = get_excluded_samples(process)
        performances_dict = calculate_performances(cluster_dict, excluded_samples)
        dx_analytes = process.analytes()[0]

        for dx_analyte in dx_analytes:
            if dx_analyte not in excluded_samples:
                input_artifact = dx_analyte.input_artifact_list()[0]
                if input_artifact.container.name == input_container:
                    samplename = dx_analyte.name.split('_')[0]
                    size, concentration = get_qc_values_parent_process_artifact(input_artifact)
                    duplicate_process = input_artifact.parent_process
                    for duplicate_analyte in duplicate_process.analytes()[0]:
                        if (input_artifact.name.split("_")[0] == duplicate_analyte.name.split("_")[0] and
                                input_artifact.id != duplicate_analyte.id):  # _LPsrWGS fraction for same sample
                            nM_pool, volume_sample = get_info_from_LP_process(lims, lowpass_processes, duplicate_analyte)
                            performances_dict[samplename]['volume_sample'] = volume_sample
                    performance = performances_dict[samplename]['performance']
                    volume_water = calculate_volumes_nM_rediluting(nM_pool, volume_sample, size, concentration, performance)
                    volumes_dict, new_samples_excluded = check_excluding_sample(
                        dx_analyte, volume_water, performances_dict, new_samples_excluded
                    )

    info_dictionary = fill_info_dictionary(dx_analytes, input_container, volumes_dict)

    return info_dictionary, missing_samples


def generate_samplesheet_redilute(lims, process, input_containers):
    """Generates a Myra samplesheet for nM rediluting after LowPass sequencing.

    Args:
        lims (object): Lims connection
        process (object): Lims Process object
        input_containers (list): List of input container names

    Returns:
        tuple[str,list]:
        Myra Dilute samplesheet &
        List containing samplenames of samples present in QC stats LowPass file, but not in process analytes
    """
    info_dictionary = {}
    for input_container in input_containers:
        info_input_dictionary, missing_samples = get_info_for_samplesheet_redilute(lims, process, input_container)
        info_dictionary.update(info_input_dictionary)
    sorted_info_dictionary = sort_dict_by_nested_well_location(
        info_dictionary, "well_output", "96_well_plate"
    )
    samplesheet_content = {"samples": sorted_info_dictionary}
    samplesheet = create_samplesheet("Samplesheet_Myra_Dilute.csv", samplesheet_content)

    return samplesheet, missing_samples


def get_input_containers_and_generate_samplesheet_redilute(lims, process_id, output_file):
    """Gets all input_containers and generates a redilute samplesheet.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): File path for samplesheet
    """
    process = Process(lims, id=process_id)
    input_containers = get_input_containers(process)
    samplesheet, missing_samples = generate_samplesheet_redilute(lims, process, input_containers)

    output_file.write(samplesheet)

    if missing_samples:
        message = (
            'De volgende samples staan wel in het QC stats LowPass bestand, '
            f'maar zijn niet aanwezig in deze stap (clusters niet meegenomen in de berekening): {missing_samples}'
        )
        sys.exit(message)
