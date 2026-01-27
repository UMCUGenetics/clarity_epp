"""Plate  placement functions."""
from genologics.entities import Process, Container, Containertype


def copy_placement(lims, process_id):
    """
    Copy placement layout from previous steps.
    
      Args:
        lims (object): Lims connection
        process_id (str): Process ID

    Returns:
        dict: Sample name and placement from the parent container.
        Container | None: The parent container the placements were copied from, or None if not found.
    """
    process = Process(lims, id=process_id)
    # Get parent container layout
    parent_container = None
    for parent_process in process.parent_processes():
        if parent_process:
            for container in parent_process.output_containers():
                if container.type != Containertype(lims, id='2'):  # skip tubes
                    parent_container = container

    if parent_container:
        parent_placements = {}
        for placement in parent_container.placements:
            sample = parent_container.placements[placement].samples[0].name
            parent_placements[sample] = placement
    return parent_placements, parent_container

def copy_layout_to_new_container(lims, process_id):
    """
    Creates a new container and copies sample placements previous step.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID

    """
    process = Process(lims, id=process_id)
    parent_placements, parent_container = copy_placement(lims, process_id)
    if parent_container:
        # Create new container and copy layout
        new_container = Container.create(lims, type=parent_container.type)
        used_placements = []
        placement_list = []
        for artifact in process.analytes()[0]:
            sample_name = artifact.samples[0].name
            if sample_name in parent_placements:
                placement = parent_placements[sample_name]
                if placement not in used_placements:
                    placement_list.append([artifact, (new_container, placement)])
                    used_placements.append(placement)
        process.step.placements.set_placement_list(placement_list)
        process.step.placements.post()

def copy_layout_to_two_new_container(lims, process_id):
    """
    Creates a two new containes and copies sample placements previous step.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID

    """
    process = Process(lims, id=process_id)
    parent_placements, parent_container = copy_placement(lims, process_id)
    if parent_container:
        for placement in parent_container.placements:
            sample = parent_container.placements[placement].samples[0].name
            parent_placements[sample] = placement

        # Create two new container and copy layout
        lowpass_container = Container.create(lims, type=parent_container.type)
        srwgs_container = Container.create(lims, type=parent_container.type)

        # Rename output containers
        base_name = parent_container.name
        lowpass_container.name = f"{base_name}_LPsrWGS"
        srwgs_container.name = f"{base_name}_srWGS"
        lowpass_container.put()
        srwgs_container.put()

        used_placements = []
        placement_list_srwgs = []
        placement_list_lp = []
        artifacts_by_sample = {}
        #2 Artifacts per sample (srWGS and lowpass)
        for artifact in process.analytes()[0]:
            sample_name = artifact.samples[0].name

            if sample_name not in artifacts_by_sample:
                artifacts_by_sample[sample_name] = []

            artifacts_by_sample[sample_name].append(artifact)
        # Place samples in both containers
        for artifact in process.analytes()[0]:
            sample_name = artifact.samples[0].name

            if sample_name in parent_placements:
                placement = parent_placements[sample_name]
                if placement not in used_placements:
                    placement_list_srwgs.append([artifacts_by_sample[sample_name][0], (srwgs_container, placement)])
                    placement_list_lp.append([artifacts_by_sample[sample_name][1], (lowpass_container, placement)]) 


                    used_placements.append(placement)

        combined = placement_list_srwgs + placement_list_lp
        process.step.placements.set_placement_list(combined)
        process.step.placements.post()


def get_layout_multiple_input_containers(process):
    """Gets layout from multiple input containers

    Args:
        process (object): Lims Process object

    Returns:
        dict: Nested dictionary with samplename per placement per input container
    """
    layout_input_containers = {}
    input_artifacts = process.all_inputs()

    for input_artifact in input_artifacts:
        container = input_artifact.container.name
        placement = input_artifact.location[1]
        if container in layout_input_containers:
            layout_input_containers[container][placement] = input_artifact.samples[0].name
        else:
            layout_input_containers[container] = {placement: input_artifact.samples[0].name}

    return layout_input_containers


def transpose_placements_row_to_column(layout_input_containers):
    """Transposes given sample placements from row to column

    Args:
        layout_input_containers (dict): Nested dictionary with samplename per placement per input container

    Returns:
        dict: Dictionary with transposed placement per samplename
    """
    rows = list(map(chr, range(ord('A'), ord('H')+1)))
    row_to_column = {
        1: {'A': 1, 'B': 2, 'C': 3}, 2: {'A': 4, 'B': 5, 'C': 6}, 3: {'A': 7, 'B': 8, 'C': 9}, 4: {'A': 10, 'B': 11, 'C': 12}
    }
    output_well_per_sample = {}
    number_of_input_containers = len(layout_input_containers.keys())

    for i in range(0, number_of_input_containers):
        input_number = i+1
        input_name = sorted(layout_input_containers.keys())[i]
        for input_well in sorted(layout_input_containers[sorted(layout_input_containers.keys())[i]]):
            output_row = rows[int(input_well[-1]) - 1]
            output_column = str(row_to_column[input_number][input_well[0]])
            output_well = ':'.join([output_row, output_column])
            output_well_per_sample[layout_input_containers[input_name][input_well]] = output_well

    return output_well_per_sample


def create_container_and_place_samples(lims, process, sample_placements, container_type_name):
    """Creates new output container with given type and places samples based on given sample placements

    Args:
        lims (object): Lims connection
        process (object): Lims Process object
        sample_placements (dict): Dictionary with adjusted placement per samplename
        container_type_name (str): Type name of new output container
    """
    container_type = lims.get_container_types(name=container_type_name)[0]
    new_container = Container.create(lims, type=container_type)
    used_placements = []
    placement_list = []

    for artifact in process.analytes()[0]:
        sample_name = artifact.samples[0].name
        if sample_name in sample_placements:
            placement = sample_placements[sample_name]
            if placement not in used_placements:
                placement_list.append([artifact, (new_container, placement)])
                used_placements.append(placement)

    process.step.placements.set_placement_list(placement_list)
    process.step.placements.post()


def copy_placement_row_to_column(lims, process_id):
    """Copies input container layout, transposes sample placement from row to column and places samples on new output container

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
    """
    process = Process(lims, id=process_id)

    layout_input_containers = get_layout_multiple_input_containers(process)
    output_well_per_sample = transpose_placements_row_to_column(layout_input_containers)
    create_container_and_place_samples(lims, process, output_well_per_sample, '96 well plate')

