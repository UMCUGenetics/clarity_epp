"""Plate  placement functions."""

from genologics.entities import Process, Container


def copy_layout(lims, process_id):
    """Copy placement layout from previous steps."""
    process = Process(lims, id=process_id)

    # Get parent container layout
    parent_container = process.parent_processes()[0].output_containers()[0]
    parent_placements = {}
    for placement in parent_container.placements:
        sample = parent_container.placements[placement].samples[0].name
        parent_placements[sample] = placement

    # Create new container and copy layout
    new_container = Container.create(lims, type=parent_container.type)
    placement_list = []
    for artifact in process.all_outputs():
        placement = parent_placements[artifact.samples[0].name]

        placement_list.append([artifact, (new_container, placement)])

    process.step.placements.set_placement_list(placement_list)
    process.step.placements.post()
