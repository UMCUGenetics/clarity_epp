"""Sample upload epp functions."""
from datetime import datetime
import re
from requests.exceptions import ConnectionError
import sys

from genologics.entities import Sample, Project, Containertype, Container

from .. import send_email
import clarity_epp.upload.utils
import config


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
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
        sys.exit(message)

    # Get researcher using helix initials
    for researcher in lims.get_researchers():
        # Use FAX as intials field as the lims initials field can't be edited via the 5.0 web interface.
        if researcher.fax == helix_initials:
            email_settings['to_import_helix'].append(researcher.email)
            break
    else:   # No researcher found
        subject = "ERROR Lims Helix Upload: {0}".format(project_name)
        message = "Can't find researcher with initials: {0}.".format(helix_initials)
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
        sys.exit(message)

    # Create project
    if not lims.get_projects(name=project_name):
        project = Project.create(lims, name=project_name, researcher=researcher, udf={'Application': 'DX'})
    else:
        subject = "ERROR Lims Helix Upload: {0}".format(project_name)
        message = "Duplicate project / werklijst. Samples not loaded."
        # send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
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
        'Dx Foetus ID': {'column': 'Foet_id'},
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
        'Dx Einddatum': {'column': 'Einddatum'},
        'Dx Gerelateerde onderzoeken': {'column': 'Gerelateerde onderzoeken'},
        'Dx gerelateerd aan oz': {'column': 'Gerelateerd aan'},
        'Dx gerelateerde oz #': {'column': 'Aantal gerelateerde onderzoeken.'},
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

        udf_data = {'Sample Type': 'DNA isolated', 'Dx Import warning': '', 'Dx Exoomequivalent': 1}  # required lims input
        for udf in udf_column:
            # Transform specific udf
            if udf in ['Dx Overleden', 'Dx Spoed', 'Dx NICU Spoed']:
                udf_data[udf] = clarity_epp.upload.utils.txt_to_bool(data[udf_column[udf]['index']])
            elif udf in ['Dx Geslacht', 'Dx Foetus geslacht']:
                udf_data[udf] = clarity_epp.upload.utils.transform_sex(data[udf_column[udf]['index']])
            elif udf == 'Dx Foetus':
                udf_data[udf] = bool(data[udf_column[udf]['index']].strip())
            elif udf == 'Dx Concentratie (ng/ul)':
                udf_data[udf] = data[udf_column[udf]['index']].replace(',', '.')
                if udf_data[udf]:
                    udf_data[udf] = float(udf_data[udf])
            elif udf in ['Dx Monsternummer', 'Dx Fractienummer']:
                udf_data[udf] = clarity_epp.upload.utils.transform_sample_name(data[udf_column[udf]['index']])
            elif udf == 'Dx Gerelateerde onderzoeken':
                udf_data[udf] = data[udf_column[udf]['index']].replace(',', ';')
            elif udf == 'Dx Einddatum':
                date = datetime.strptime(data[udf_column[udf]['index']], '%d-%m-%Y')  # Helix format (14-01-2021)
                udf_data[udf] = date.strftime('%Y-%m-%d')  # LIMS format (2021-01-14)
            else:
                udf_data[udf] = data[udf_column[udf]['index']]

        sample_name = '{0}_{1}'.format(udf_data['Dx Monsternummer'], udf_data['Dx Meet ID'])

        # Set 'Dx Handmatig' udf
        if (
            udf_data['Dx Foetus']
            or udf_data['Dx Overleden']
            or udf_data['Dx Materiaal type'] not in ['BL', 'BLHEP', 'BM', 'BMEDTA']
            or re.match(r'\d{4}D\d+', udf_data['Dx Monsternummer']) and int(udf_data['Dx Monsternummer'][:4]) < 2010  # Samples older then 2010
            or udf_data['Dx Monsternummer'].startswith('D')  # Old samples names, all older then 2005
        ):
            udf_data['Dx Handmatig'] = True
        else:
            udf_data['Dx Handmatig'] = False

        # Set 'Dx norm. manueel' udf
        if udf_data['Dx Concentratie (ng/ul)'] and udf_data['Dx Concentratie (ng/ul)'] < 29.3:
            udf_data['Dx norm. manueel'] = True
        else:
            udf_data['Dx norm. manueel'] = False

        # Set 'Dx Familie status' udf
        if udf_data['Dx Onderzoeksreden'] == 'Bevestiging diagnose':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Prenataal onderzoek':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Eerstegraads-verwantenond':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Partneronderzoek':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Dragerschapbepaling':
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Presymptomatisch onderzoe':  # Helix export is truncated (Presymptomatisch onderzoek)
            udf_data['Dx Familie status'] = 'Kind'
        elif udf_data['Dx Onderzoeksreden'] == 'Informativiteitstest':
            udf_data['Dx Familie status'] = 'Ouder'
        else:
            udf_data['Dx Import warning'] = '; '.join([
                'Onbekende onderzoeksreden, familie status niet ingevuld.',
                udf_data['Dx Import warning']
            ])

        # Set 'Dx Geslacht' and 'Dx Geboortejaar' with 'Foetus' information if 'Dx Foetus == True'
        if udf_data['Dx Foetus']:
            udf_data['Dx Geslacht'] = udf_data['Dx Foetus geslacht']
            udf_data['Dx Geboortejaar'] = ''

        # Set 'Dx Geslacht = Onbekend' if 'Dx Onderzoeksindicatie == DSD00'
        if udf_data['Dx Onderzoeksindicatie'] == 'DSD00' and udf_data['Dx Familie status'] == 'Kind':
            udf_data['Dx Geslacht'] = 'Onbekend'

        # Check 'Dx Familienummer' and correct
        if '/' in udf_data['Dx Familienummer']:
            udf_data['Dx Import warning'] = '; '.join([
                'Meerdere familienummers, laatste wordt gebruikt. ({0})'.format(udf_data['Dx Familienummer']),
                udf_data['Dx Import warning']
            ])
            udf_data['Dx Familienummer'] = udf_data['Dx Familienummer'].split('/')[-1].strip(' ')

        # Set NICU status for related samples using Dx Gerelateerde onderzoeken
        if udf_data['Dx NICU Spoed']:
            for related_research in udf_data['Dx Gerelateerde onderzoeken'].split(';'):
                for related_sample in lims.get_samples(udf={'Dx Onderzoeknummer': related_research}):
                    related_sample.udf['Dx NICU Spoed'] = udf_data['Dx NICU Spoed']
                    related_sample.put()
        # Set NICU status for sample if related sample is NICU
        else:
            for related_sample in lims.get_samples(udf={'Dx Familienummer': udf_data['Dx Familienummer']}):
                if (
                    'Dx Gerelateerde onderzoeken' in related_sample.udf and
                    udf_data['Dx Onderzoeknummer'] in related_sample.udf['Dx Gerelateerde onderzoeken']
                ):
                    udf_data['Dx NICU Spoed'] = related_sample.udf['Dx NICU Spoed']

        # Set 'Dx Mengfractie'
        if udf_data['Dx Stoftest code'] == config.stoftestcode_wes_duplo:
            udf_data['Dx Mengfractie'] = True
            for duplo_sample in lims.get_samples(udf={
                'Dx Persoons ID': udf_data['Dx Persoons ID'],
                'Dx Onderzoeknummer': udf_data['Dx Onderzoeknummer']
            }):
                duplo_sample.udf['Dx Mengfractie'] = True
                duplo_sample.put()

        elif udf_data['Dx Stoftest code'] == config.stoftestcode_wes:
            if lims.get_samples(udf={
                'Dx Persoons ID': udf_data['Dx Persoons ID'],
                'Dx Onderzoeknummer': udf_data['Dx Onderzoeknummer'],
                'Dx Mengfractie': True
            }):
                udf_data['Dx Mengfractie'] = True
            else:
                udf_data['Dx Mengfractie'] = False

        # Check other samples from patient
        sample_list = lims.get_samples(udf={'Dx Persoons ID': udf_data['Dx Persoons ID']})
        for sample in sample_list:
            if sample.udf['Dx Monsternummer'] == udf_data['Dx Monsternummer']:
                if (
                    sample.udf['Dx Protocolomschrijving'] in udf_data['Dx Protocolomschrijving']
                    and sample.udf['Dx Foetus'] == udf_data['Dx Foetus']
                ):
                    udf_data['Dx Import warning'] = '; '.join([
                        '{sample}: Monsternummer hetzelfde, Protocolomschrijving hetzelfde.'.format(sample=sample.name),
                        udf_data['Dx Import warning']
                    ])
                else:
                    udf_data['Dx Import warning'] = '; '.join([
                        '{sample}: Monsternummer hetzelfde, Protocolomschrijving uniek.'.format(sample=sample.name),
                        udf_data['Dx Import warning']
                    ])
            elif (
                sample.udf['Dx Protocolomschrijving'] in udf_data['Dx Protocolomschrijving']
                and sample.udf['Dx Foetus'] == udf_data['Dx Foetus']
            ):
                udf_data['Dx Import warning'] = '; '.join([
                    '{sample}: Monsternummer uniek, Protocolomschrijving hetzelfde.'.format(sample=sample.name),
                    udf_data['Dx Import warning']
                ])

        # Add sample to workflow
        workflow = clarity_epp.upload.utils.stoftestcode_to_workflow(lims, udf_data['Dx Stoftest code'])
        if workflow:
            container = Container.create(lims, type=container_type, name=udf_data['Dx Fractienummer'])
            sample = Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
            lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
            if udf_data['Dx Import warning']:
                message += "{0}\tCreated and added to workflow: {1}.\tImport warning: {2}\n".format(
                    sample.name,
                    workflow.name,
                    udf_data['Dx Import warning']
                )
            else:
                message += "{0}\tCreated and added to workflow: {1}.\n".format(sample.name, workflow.name)
        else:
            message += "{0}\tERROR: Stoftest code {1} is not linked to a workflow.\n".format(
                sample_name,
                udf_data['Dx Stoftest code']
            )

    # # Send final email
    # send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
    print(subject)
    print(message)
