"""Consumables placement functions."""

from genologics.entities import Process


def get_consumable_info_to_check(process):
    """Gets consumables information from given process

    Args:
        process (object): Lims Process object

    Returns:
        dict: Dictionary containing information about scanned and used consumables
    """
    info_dictionary = {"process_udfs": {}, "input_strip": {}, "output_strip": {}}
    info_dictionary["process_udfs"] = {
        "scan_input_strip": process.udf["Controle scan: Input strip"],
        "scan_output_strip": process.udf["Controle scan: Output strip"],
        "scan_index_strip": process.udf["Controle scan: index strip"],
        "index_strip": process.udf["Index strip barcode"]
    }
    input_artifacts = process.all_inputs()
    for input_artifact in input_artifacts:
        info_dictionary["input_strip"][input_artifact.name] = input_artifact.container.name
    output_analytes = process.analytes()[0]
    for output_analyte in output_analytes:
        info_dictionary["output_strip"][output_analyte.name] = output_analyte.container.name
    return info_dictionary


def perform_consumables_check(process, info_dictionary):
    """Performs checks if scanned consumables are the same as used consumables for every analyte;
    if the scans are the same as the used consumables udf "Dx consumables check" will be set to True

    Args:
        process (object): Lims Process object
        info_dictionary (dict): Dictionary containing information about scanned and used consumables
    """
    if info_dictionary["process_udfs"]["scan_index_strip"] == info_dictionary["process_udfs"]["index_strip"]:
        analytes = process.analytes()[0]
        for analyte in analytes:
            if (info_dictionary["process_udfs"]["scan_input_strip"] == info_dictionary["input_strip"][analyte.name] and
                    info_dictionary["process_udfs"]["scan_output_strip"] == info_dictionary["output_strip"][analyte.name]):
                analyte.udf["Dx consumables check"] = True
                analyte.put()


def check_used_consumables(lims, process_id):
    """Checks consumables for every analyte

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
    """
    process = Process(lims, id=process_id)
    info_dictionary = get_consumable_info_to_check(process)
    perform_consumables_check(process, info_dictionary)
