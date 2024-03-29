from genologics.entities import Process, Container, Containertype


def get_well_location(index):
    locations = [
        'A:1', 'B:1', 'C:1', 'D:1', 'E:1', 'F:1', 'G:1', 'H:1',
        'A:2', 'B:2', 'C:2', 'D:2', 'E:2', 'F:2', 'G:2', 'H:2',
        'A:3', 'B:3', 'C:3', 'D:3', 'E:3', 'F:3', 'G:3', 'H:3',
        'A:4', 'B:4', 'C:4', 'D:4', 'E:4', 'F:4', 'G:4', 'H:4',
        'A:5', 'B:5', 'C:5', 'D:5', 'E:5', 'F:5', 'G:5', 'H:5',
        'A:6', 'B:6', 'C:6', 'D:6', 'E:6', 'F:6', 'G:6', 'H:6',
        'A:7', 'B:7', 'C:7', 'D:7', 'E:7', 'F:7', 'G:7', 'H:7',
        'A:8', 'B:8', 'C:8', 'D:8', 'E:8', 'F:8', 'G:8', 'H:8',
        'A:9', 'B:9', 'C:9', 'D:9', 'E:9', 'F:9', 'G:9', 'H:9',
        'A:10', 'B:10', 'C:10', 'D:10', 'E:10', 'F:10', 'G:10', 'H:10',
        'A:11', 'B:11', 'C:11', 'D:11', 'E:11', 'F:11', 'G:11', 'H:11',
        'A:12', 'B:12', 'C:12', 'D:12', 'E:12', 'F:12', 'G:12', 'H:12'
    ]
    return locations[index]


def place_artifacts(lims, process_id):
    """Place artifacts on two containers, 2 artifacts per sample."""
    process = Process(lims, id=process_id)

    # Create containers
    well_plate = Containertype(lims, id='1')
    purify_container = Container.create(lims, type=well_plate)
    normalise_container = Container.create(lims, type=well_plate)
    purify_container.name = "zuiveren_{id}".format(id=purify_container.name)
    normalise_container.name = "normaliseren_{id}".format(id=normalise_container.name)
    purify_container.put()
    normalise_container.put()

    # Keep track of placements
    container_placement = {}
    placement_list = []

    # Place all artifacts
    for artifact in process.analytes()[0]:
        if artifact.name not in container_placement:  # Add first artifact to purify_container
            well_location = get_well_location(len(container_placement))
            placement_list.append([artifact, (purify_container, well_location)])
            container_placement[artifact.name] = well_location
        else:  # Add second artifact to normalise_container on same position
            well_location = container_placement[artifact.name]
            placement_list.append([artifact, (normalise_container, well_location)])

    process.step.placements.set_placement_list(placement_list)
    process.step.placements.post()
