"""Bioanalyzer export functions."""

from genologics.entities import Process


def samplesheet(lims, process_id, output_file):
    """Create Bioanalyzer samplesheet."""
    process = Process(lims, id=process_id)

    # Default plate layout
    plate = {
        'A1': {'name': 'sample 1', 'comment': 'HP+'}, 'A2': {'name': 'sample 2', 'comment': 'HP+'}, 'A3': {'name': 'sample 3', 'comment': 'HP+'},
        'B1': {'name': 'sample 4', 'comment': 'HP+'}, 'B2': {'name': 'sample 5', 'comment': 'HP+'}, 'B3': {'name': 'sample 6', 'comment': 'HP+'},
        'C1': {'name': 'sample 7', 'comment': 'HP+'}, 'C2': {'name': 'sample 8', 'comment': 'HP+'}, 'C3': {'name': 'sample 9', 'comment': 'HP+'},
        'D1': {'name': 'sample 10', 'comment': 'HP+'}, 'D2': {'name': 'sample 11', 'comment': 'HP+'}
    }

    # Get sample placement
    for placement, artifact in process.output_containers()[0].placements.iteritems():
        placement = ''.join(placement.split(':'))
        plate[placement]['name'] = artifact.name
        plate[placement]['comment'] = ''

    # Create samplesheet
    output_file.write('"Sample Name","Sample Comment","Rest. Digest","Status","Observation","Result Label","Result Color"\n')
    for well in sorted(plate.keys()):
        output_file.write('{sample},{sample_comment},FALSE,1,,,\n'.format(
            sample=plate[well]['name'],
            sample_comment=plate[well]['comment']
        ))
    output_file.write('Ladder,,FALSE,1,,,\n\n')

    output_file.write('"Chip Lot #","Reagent Kit Lot #"\n')
    output_file.write('{chip_lot},{reagent_lot}\n\n'.format(
        chip_lot=process.udf['lot # chip'],
        reagent_lot=process.udf['lot # Reagentia kit']
    ))

    output_file.write('"QC1 Min [%]","QC1 Max [%]","QC2 Min [%]","QC2 Max [%]"\n')
    output_file.write(',,,\n\n')

    output_file.write('"Chip Comment"\n\n\n')

    output_file.write('"Study Name","Experimenter","Laboratory","Company","Department"\n')
    output_file.write(',,,,\n\n')

    output_file.write('"Study Comment"\n\n')
