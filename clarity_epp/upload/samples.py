"""Sample upload epp functions."""
import sys

from requests.exceptions import ConnectionError
from genologics.entities import Sample, Project, Containertype, Container

from .. import send_email
import utils


def from_helix(lims, email_settings, input_file):
    """Upload samples from helix export file."""
    project_name = 'Dx {filename}'.format(filename=input_file.name.rstrip('.csv').split('/')[-1])
    helix_initials = project_name.split('_')[-1]

    # Try lims connection
    try:
        lims.check_version()
    except ConnectionError:
        subject = "ERROR Lims Helix Upload: {0}".format(project_name)
        message = "Can't connect to lims server, please contact a lims administrator."
        send_email(email_settings['from'], email_settings['to'], subject, message)
        sys.exit(message)

    # Get researcher using helix initials
    for researcher in lims.get_researchers():
        if researcher.fax == helix_initials:  # Use FAX as intials field as the lims initials field can't be edited via the 5.0 web interface.
            email_settings['to'].append(researcher.email)
            break
    else:   # No researcher found
        subject = "ERROR Lims Helix Upload: {0}".format(project_name)
        message = "Can't find researcher with initials: {0}.".format(helix_initials)
        send_email(email_settings['from'], email_settings['to'], subject, message)
        sys.exit(message)

    # Create project
    if not lims.get_projects(name=project_name):
        project = Project.create(lims, name=project_name, researcher=researcher, udf={'Application': 'DX'})
    else:
        subject = "ERROR Lims Helix Upload: {0}".format(project_name)
        message = "Duplicate project / werklijst. Samples not loaded."
        send_email(email_settings['from'], email_settings['to'], subject, message)
        sys.exit(message)

    container_type = Containertype(lims, id='2')  # Tube

    # match header and udf fields
    udf_column = {
        'Dx Onderzoeknummer': {'column': 'Onderzoeknummer'},
        'Dx Fractienummer': {'column': 'Fractienummer'},
        'Dx Monsternummer': {'column': 'Monsternummer'},
        'Dx Concentratie (ng/ul)': {'column': 'Concentratie (ng/ul)'},
        'Dx Materiaal type': {'column': 'Materiaal'},
        'Dx Foetus': {'column': 'Foetus'},
        'Dx Foetus geslacht': {'column': 'Foetus_geslacht'},
        'Dx Overleden': {'column': 'Overleden'},
        'Dx Opslaglocatie': {'column': 'Opslagpositie'},
        'Dx Spoed': {'column': 'Spoed'},
        'Dx NICU Spoed': {'column': 'NICU Spoed'},
        'Dx Persoons ID': {'column': 'Persoons_id'},
        'Dx Werklijstnummer': {'column': 'Werklijstnummer'},
        'Dx Familienummer': {'column': 'Familienummer'},
        'Dx Geslacht': {'column': 'Geslacht'},
        'Dx Geboortejaar': {'column': 'Geboortejaar'},
        'Dx Meet ID': {'column': 'Stof_meet_id'},
        'Dx Stoftest code': {'column': 'Stoftestcode'},
        'Dx Stoftest omschrijving': {'column': 'Stoftestomschrijving'},
        'Dx Onderzoeksindicatie': {'column': 'Onderzoeksindicatie'},
        'Dx Onderzoeksreden': {'column': 'Onderzoeksreden'},
        'Dx Protocolcode': {'column': 'Protocolcode'},
        'Dx Protocolomschrijving': {'column': 'Protocolomschrijving'},
    }
    header = input_file.readline().rstrip().split(',')  # expect header on first line
    for udf in udf_column:
        udf_column[udf]['index'] = header.index(udf_column[udf]['column'])

    # Setup email
    subject = "Lims Helix Upload: {0}".format(project_name)
    message = "Project: {0}\n\nSamples:\n".format(project_name)

    # Parse samples
    for line in input_file:
        data = line.rstrip().strip('"').split('","')
        sample_name = data[header.index('Monsternummer')]

        udf_data = {'Sample Type': 'DNA isolated', 'Dx Import warning': ''}  # required lims input
        for udf in udf_column:
            # Transform specific udf
            if udf in ['Dx Overleden', 'Dx Spoed', 'Dx NICU Spoed']:
                udf_data[udf] = utils.char_to_bool(data[udf_column[udf]['index']])
            elif udf in ['Dx Geslacht', 'Dx Foetus geslacht']:
                udf_data[udf] = utils.transform_sex(data[udf_column[udf]['index']])
            elif udf == 'Dx Foetus':
                udf_data[udf] = bool(data[udf_column[udf]['index']].strip())
            elif udf == 'Dx Concentratie (ng/ul)':
                udf_data[udf] = data[udf_column[udf]['index']].replace(',', '.')
            else:
                udf_data[udf] = data[udf_column[udf]['index']]

        # Set 'Dx Handmatig' udf
        if udf_data['Dx Foetus'] or udf_data['Dx Overleden'] or udf_data['Dx Materiaal type'] != 'BL':
            udf_data['Dx Handmatig'] = True
        else:
            udf_data['Dx Handmatig'] = False

        # Set 'Dx Familie status' udf
        if udf_data['Dx Onderzoeksreden'] == 'Bevestiging diagnose':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Prenataal onderzoek':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Informativiteitstest':
            udf_data['Dx Familie status'] = 'Ouder'
        else:
            udf_data['Dx Import warning'] = ';'.join(['Onbekende onderzoeksreden, familie status niet ingevuld.', udf_data['Dx Import warning']])

        # Set 'Dx Geslacht' and 'Dx Geboortejaar' with 'Foetus' information if 'Dx Foetus == True'
        if udf_data['Dx Foetus']:
            udf_data['Dx Geslacht'] = udf_data['Dx Foetus geslacht']
            udf_data['Dx Geboortejaar'] = ''

        # Set 'Dx Geslacht = Onbekend' if 'Dx Onderzoeksindicatie == DSD00'
        if udf_data['Dx Onderzoeksindicatie'] == 'DSD00':
            udf_data['Dx Geslacht'] = 'Onbekend'

        # Check 'Dx Familienummer' and correct
        if '/' in udf_data['Dx Familienummer']:
            udf_data['Dx Import warning'] = ';'.join([
                'Meerdere familienummers, laatste wordt gebruikt. ({0})'.format(udf_data['Dx Familienummer']),
                udf_data['Dx Import warning']
            ])
            udf_data['Dx Familienummer'] = udf_data['Dx Familienummer'].split('/')[-1].strip(' ')

        sample_list = lims.get_samples(name=sample_name)

        if sample_list:
            sample = sample_list[0]
            if udf_data['Dx Protocolomschrijving'] in sample.udf['Dx Protocolomschrijving']:
                message += "{0}\tERROR: Duplicate sample and Protocolomschrijving code: {1}.\n".format(sample_name, udf_data['Dx Protocolomschrijving'])
            else:
                # Update existing sample if new Protocolomschrijving and thus workflow.

                # Append udf fields
                append_udf = [
                    'Dx Onderzoeknummer', 'Dx Onderzoeksindicatie', 'Dx Onderzoeksreden', 'Dx Werklijstnummer', 'Dx Protocolcode', 'Dx Protocolomschrijving',
                    'Dx Meet ID', 'Dx Stoftest code', 'Dx Stoftest omschrijving'
                ]
                for udf in append_udf:
                    sample.udf[udf] = ';'.join([udf_data[udf], str(sample.udf[udf])])

                # Update udf fields
                update_udf = ['Dx Overleden', 'Dx Spoed', 'Dx NICU Spoed', 'Dx Handmatig', 'Dx Opslaglocatie', 'Dx Import warning']
                for udf in update_udf:
                    sample.udf[udf] = udf_data[udf]

                # Add to new workflow
                workflow = utils.stofcode_to_workflow(lims, udf_data['Dx Stoftest code'])
                if workflow:
                    sample.put()
                    lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
                    message += "{0}\tUpdated and added to workflow: {1}.\n".format(sample.name, workflow.name)
                else:
                    message += "{0}\tERROR: Stoftest code {1} is not linked to a workflow.\n".format(sample.name, udf_data['Dx Stoftest code'])

        else:
            # Check other samples from patient
            sample_list = lims.get_samples(udf={'Dx Persoons ID': udf_data['Dx Persoons ID']})
            for sample in sample_list:
                if sample.udf['Dx Protocolomschrijving'] == udf_data['Dx Protocolomschrijving'] and sample.udf['Dx Foetus'] == udf_data['Dx Foetus']:
                    udf_data['Dx Import warning'] = ';'.join(['Onderzoek reeds uitgevoerd.', udf_data['Dx Import warning']])

            # Add sample to workflow
            workflow = utils.stofcode_to_workflow(lims, udf_data['Dx Stoftest code'])
            if workflow:
                container = Container.create(lims, type=container_type, name=udf_data['Dx Fractienummer'])
                sample = Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
                lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
                message += "{0}\tCreated and added to workflow: {1}.\n".format(sample.name, workflow.name)
            else:
                message += "{0}\tERROR: Stoftest code {1} is not linked to a workflow.\n".format(sample_name, udf_data['Dx Stoftest code'])

    # Send final email
    send_email(email_settings['from'], email_settings['to'], subject, message)
