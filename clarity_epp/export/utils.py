"""Utility functions used for creating samplesheets."""
import re

from jinja2 import Environment, PackageLoader


def sort_96_well_plate(wells):
    """Sort 96 well plate wells in vertical order.

    Arguments:
    wells -- unordered list of wells: ['A1', 'C1', 'E1', 'B1', 'D1']

    """
    order = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1',
        'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
        'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5',
        'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7',
        'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9',
        'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11',
        'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]
    order = dict(zip(order, range(len(order))))

    wells = sorted(wells, key=lambda val: order[val])
    return wells


def reverse_complement(dna_sequence):
    """Return reverse complement DNA sequence."""
    complement = [{'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}[base] for base in dna_sequence]
    reverse_complement = reversed(complement)
    return ''.join(reverse_complement)


def sort_artifact_list(artifact):
    if '-' in artifact.id:
        return int(artifact.id.split('-')[1])
    else:
        return -1


def get_process_types(lims, process_types_names):
    """Get process types by partial name.

    If complete name is known use lims.get_process_types(displayname="complete name")
    """
    all_process_types = lims.get_process_types()
    process_types = []

    for process_type in all_process_types:
        for process_types_name in process_types_names:
            if process_types_name in process_type.name:
                process_types.append(process_type.name)

    return process_types


def get_well_index(well, one_based=False):
    """Return well index

    Arguments:
    well -- well str: 'A1'

    """
    wells = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1',
        'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
        'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5',
        'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7',
        'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9',
        'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11',
        'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]

    if one_based:
        return wells.index(well) + 1
    else:
        return wells.index(well)


def get_sample_sequence_index(reagent_label):
    """Return sample sequence indices [index1, index2] from reagent label.
    expected reagent label pattern = "<index name> (index1-index2)" or "<index name> (index1)"
    """
    sample_index_search = re.search(r"\(([ACTGN-]+)\)$", reagent_label)
    sample_index = sample_index_search.group(1).split('-')

    return sample_index


def extract_well_from_reagent_label(reagent_label):
    """Extracts and returns the well location from the given reagent label name
    by splitting the reagent label name (spaces), taking the second string ("01A"),
    removing the first 0 if present ("1A") and changing the order ("A1").

    Args:
        reagent_label (str): Reagent label name (format example: "Dx 01A 1057 (GAACCTGATG-AGCATATTAG)")

    Returns:
        str: Well location extracted from reagent label
    """
    label_location = reagent_label.split(" ")[1]
    if label_location.startswith("0"):
        # remove starting 0 for columns 1-9
        label_location = label_location[1:]
    return label_location[-1] + label_location[:-1]


def create_samplesheet(template_file, variable_content, environment=Environment(loader=PackageLoader("clarity_epp"))):
    """Gets samplesheet template and fills with the information from the given variable content dictionary.

    Args:
        template_file (str): Samplesheet template file name
        variable_content (dict): Dictionary (nested) with samplesheet content (first key(s) needs to be a string)
        environment (object, optional): jinja2.environment.Environment object.
            Defaults to Environment(loader=PackageLoader("clarity_epp")).

    Returns:
        str: Filled samplesheet template
    """
    template = environment.get_template(template_file)
    samplesheet = template.render(variable_content)

    return samplesheet


def sort_dict_by_nested_well_location(dict_to_sort, key_to_sort_by, container="96_well_plate"):
    """Sorts a given dictionary by well location stored as value in nested dictionary;
    format dictionary: dict_to_sort[key][key_to_sort_by] = well (e.g. A1)

    Args:
        dict_to_sort (dict): Dictionary to sort by well location
        key_to_sort_by (str): The key containing the well location value to sort by
        container (str): Container type for sorting ("24_well_barcoded_callisto_strip", default="96_well_plate")

    Returns:
        dict: Sorted dictionary
    """
    used_wells = []
    for key in dict_to_sort:
        used_wells.append(dict_to_sort[key][key_to_sort_by])
    if container == "96_well_plate":
        sorted_wells = sort_96_well_plate(used_wells)
    elif container == "24_well_barcoded_callisto_strip":
        sorted_wells = sort_24_well_barcoded_callisto_strip(used_wells)
    sorted_dict = {}
    for well in sorted_wells:
        for key in dict_to_sort:
            if well == dict_to_sort[key][key_to_sort_by]:
                sorted_dict[key] = dict_to_sort[key]
    return sorted_dict


def get_input_containers(process):
    """Gets input container names for the given process

    Args:
        process (object): Lims Process object

    Returns:
        list: List of process input container names
    """
    input_containers = []
    input_artifacts = process.all_inputs()
    for input_artifact in input_artifacts:
        container = input_artifact.container.name
        if container not in input_containers:
            input_containers.append(container)
    input_containers = sorted(input_containers)
    return input_containers


def sort_24_well_barcoded_callisto_strip(wells):
    """Sort 24 Wells Strip Callisto barcoded wells in horizontal order.

    Args:
        wells (list): Unordered list of wells, e.g. ['A1', 'C1', 'E1', 'B1', 'D1']
    """
    order = [
        'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
        'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
        'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'
    ]
    order = dict(zip(order, range(len(order))))

    wells = sorted(wells, key=lambda val: order[val])
    return wells


def get_qc_values_parent_process_artifact(input_artifact):
    """Gets size (fragmentlengte) and concentration (concentratie) from parent process for given artifact.

    Args:
        input_artifact (object): Lims Artifact object

    Returns:
        tuple[float,float]:
        Size (fragmentlengte), None if size not found &
        Concentration (concentratie), None if concentration not found
    """
    size = None
    concentration = None
    parent_process = input_artifact.parent_process

    for parent_artifact in parent_process.all_inputs():
        if parent_artifact.name == input_artifact.name.split("_")[0]:
            size = float(parent_artifact.udf['Dx Fragmentlengte (bp)'])
            concentration = float(parent_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

    return size, concentration


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


def get_project_applications_for_samples_in_pool(pool):
    """Gets list of all project applications of samples in a pool.

    Args:
        pool (artifact): Artifact object of a pool of samples

    Returns:
        list: List of the project applications of all samples in the given pool
    """
    applications = []
    for sample in pool.samples:
        application = sample.project.udf.get("Application")
        if application not in applications:
            applications.append(application)
    return applications


def get_artifactname_extensions_for_list_of_artifacts(artifact_list):
    """Gets artifact name extensions (artifactname_extension) for a list of artifacts

    Args:
        artifact_list (list): List of Artifact objects

    Returns:
        list: List of unique extensions (no extension will return "geen extensie")
    """
    extensions = []
    for artifact in artifact_list:
        artifact_name = artifact.name
        if "_" in artifact_name:
            extension = artifact_name.split("_")[-1]
            if extension not in extensions:
                extensions.append(extension)
        else:
            if "geen extensie" not in extensions:
                extensions.append("geen extensie")
    return extensions
