"""Bioanalyzer export functions."""

from genologics.entities import Process
from jinja2 import Environment, FileSystemLoader


def get_plate_layout(process):
    """Creates dictionary with sample name per well

    Args:
        process (object): Lims process/step

    Returns:
        dict: Dictionary with sample name per well info
    """
    # Default plate layout
    plate_layout = {
        'A1': 'sample 1', 'A2': 'sample 2', 'A3': 'sample 3', 'B1': 'sample 4', 'B2': 'sample 5', 'B3': 'sample 6',
        'C1': 'sample 7', 'C2': 'sample 8', 'C3': 'sample 9', 'D1': 'sample 10', 'D2': 'sample 11'
    }

    # Update default plate layout with artifact names
    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        plate_layout[placement] = artifact.name

    return plate_layout


def create_samplesheet(process, plate_layout):
    """Gets Bioanalyzer samplesheet template and fills with info from process/step

    Args:
        process (object): Lims process/step
        plate (dict): Dictionary with sample name per well info

    Returns:
        str: Filled samplesheet template
    """
    samplesheet_filling = {
        "plate": plate_layout,
        "chip_lot": process.udf['lot # chip'],
        "reagent_lot": process.udf['lot # Reagentia kit']
    }
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("Bioanalyzer_samplesheet.txt")
    samplesheet = template.render(samplesheet_filling)

    return samplesheet


def generate_samplesheet(lims, process_id, output_file):
    """Generate samplesheet for measuring fragment length with Bioanalyzer.

    Args:
        lims (object): Lims connection object
        process_id (str): Process ID/Step ID
        output_file (file): Samplesheet for Bioanalyzer
    """
    process = Process(lims, id=process_id)

    plate_layout = get_plate_layout(process)
    samplesheet = create_samplesheet(process, plate_layout)

    output_file.write(samplesheet)
