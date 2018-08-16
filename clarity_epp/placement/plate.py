"""Plate  placement functions."""

from genologics.entities import Process, Container, Containertype


def copy_layout(lims, process_id):
    """Copy placement layout from previous steps."""
    process = Process(lims, id=process_id)
    used_placements = []
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

        # Create new container and copy layout
        new_container = Container.create(lims, type=parent_container.type)
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
