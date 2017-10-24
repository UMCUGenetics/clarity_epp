"""Sample upload epp functions."""
from genologics.entities import Sample, Project, Containertype, Container, Researcher, Workflow

import utils


def from_helix(lims, input_file):
    """Upload samples from helix export file."""
    # Create project
    project_name = input_file.name.rstrip('.csv').split('/')[-1]
    if not lims.get_projects(name=project_name):
        researcher = Researcher(lims, id='254')  # DX_EPP user
        project = Project.create(lims, name=project_name, researcher=researcher, udf={'Application': 'DX'})

    container_type = Containertype(lims, id='2')  # Tube

    input_file.readline()  # expect header on first line, skip it.
    for line in input_file:
        data = line.rstrip().replace('"', '').split(',')
        sample_name = data[1]

        if utils.value_to_bool(data[5]) == False and utils.letter_to_bool(data[6]) == False and utils.letter_to_bool(data[8]) == False and utils.letter_to_bool(data[9]) == False and data[4] == 'BL':
            hand = False
        else:
            hand = True

        if lims.get_sample_number(name=sample_name):
            print "ERROR: Sample {sample_name} already exists.".format(sample_name=sample_name)
        else:
            udf_data = {
                'Sample Type': 'DNA isolated',  # required lims input
                'Dx Onderzoeknummer': data[0],
                'Dx Fractienummer': data[2],
                'Dx Concentratie (ng/ul)': data[3],
                'Dx Materiaal type': data[4],
                'Dx Foetus': utils.value_to_bool(data[5]),
                'Dx Overleden': utils.letter_to_bool(data[6]),
                'Dx Opslaglocatie': data[7],
                'Dx Spoed': utils.letter_to_bool(data[8]),
                'Dx NICU Spoed': utils.letter_to_bool(data[9]),
                'Dx Persoons ID': data[10],
                'Dx Werklijstnummer': data[11],
                'Dx Unummer': data[12],
                'Dx Geslacht': data[13],
                'Dx Geboortejaar': data[14],
                'Dx meet ID': data[15],
                'Dx Stoftest code': data[16],
                'Dx Stoftest omschrijving': data[17],
                'Dx Helix indicatie': data[18],
                'Dx Handmatig': hand,
            }
            container = Container.create(lims, type=container_type)
            sample = Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)

            if lims.get_sample_number(udf={'Dx Persoons ID': udf_data['Dx Persoons ID']}) > 1:
                workflow = Workflow(lims, id='352')  # Dx Aandachtspunten
            else:
                workflow = utils.stofcode_to_workflow(lims, udf_data['Dx Stoftest code'])

            lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
