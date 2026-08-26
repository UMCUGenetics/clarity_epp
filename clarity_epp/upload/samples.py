"""Sample upload epp functions."""
import re
import sys
from datetime import datetime, timedelta

from genologics.entities import Container, Containertype, Project, Sample
from requests.exceptions import ConnectionError

import clarity_epp.upload.utils
import config

from .. import send_email


def from_helix_worklist(lims, email_settings, input_file):
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
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
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
    sample_messages = {}

    # Parse samples
    for line_index, line in enumerate(input_file):
        data = line.rstrip().strip('"').split('","')

        clusters = config.clusters_per_sample
        udf_data = {
            'Sample Type': 'DNA isolated', 'Dx Import warning': '', 'Dx Exoomequivalent': 1, 'Dx # clusters/sample': clusters
        }  # required lims input
        for udf in udf_column:
            # Transform specific udf
            try:
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
            except (IndexError, ValueError):
                # Catch parsing errors and send email
                subject = "ERROR Lims Helix Upload: {0}".format(project_name)
                message = (
                    "Could not correctly parse data from helix export file (werklijst).\n"
                    f"Row = {line_index+1} \t Column = {udf_column[udf]['column']} \t UDF = {udf}.\n"
                    "Please check/update the file and try again. Make sure to remove the project from LIMS before retrying."
                )
                send_email(
                    email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message
                )
                sys.exit(message)

        sample_name = '{0}_{1}'.format(udf_data['Dx Monsternummer'], udf_data['Dx Meet ID'])

        # Set 'Dx Handmatig' udf
        if (
            udf_data['Dx Foetus']
            or udf_data['Dx Overleden']
            or udf_data['Dx Materiaal type'] not in ['BL', 'BLHEP', 'BM', 'BMEDTA']
            or re.match(r'\d{4}D\d+', udf_data['Dx Monsternummer'])
            and int(udf_data['Dx Monsternummer'][:4]) < 2010  # Samples older then 2010
            or udf_data['Dx Monsternummer'].startswith('D')  # Old samples names, all older then 2005
        ):
            udf_data['Dx Handmatig'] = True
        else:
            udf_data['Dx Handmatig'] = False

        # Set 'Dx norm. manueel' udf for samples with Dx Concentratie (ng/ul)
        if udf_data['Dx Concentratie (ng/ul)']:
            if udf_data['Dx Concentratie (ng/ul)'] <= 29.3:
                udf_data['Dx norm. manueel'] = True
            else:
                udf_data['Dx norm. manueel'] = False

        # Set 'Dx Familie status' udf
        if 'Bevestiging diagnose' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Kind'
        elif 'Prenataal onderzoek' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Kind'
        elif 'Eerstegraads-verwantenond' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Kind'
        elif 'Partneronderzoek' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Kind'
        elif 'Dragerschapbepaling' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Kind'
        # Helix export is truncated (Presymptomatisch onderzoek)
        elif 'Presymptomatisch onderzoe' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Kind'
        elif 'Informativiteitstest' in udf_data['Dx Onderzoeksreden']:
            udf_data['Dx Familie status'] = 'Ouder'
        else:
            udf_data['Dx Import warning'] = ';'.join([
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

        # Set 'Dx Exoomequivalent' for specific indications
        if udf_data['Dx Onderzoeksindicatie'] in config.indications_exome_equivalent:
            udf_data['Dx Exoomequivalent'] = config.indications_exome_equivalent[udf_data['Dx Onderzoeksindicatie']]

        # Check 'Dx Familienummer' and correct
        if '/' in udf_data['Dx Familienummer']:
            udf_data['Dx Import warning'] = ';'.join([
                'Meerdere familienummers, laatste wordt gebruikt. ({0})'.format(udf_data['Dx Familienummer']),
                udf_data['Dx Import warning']
            ])
            udf_data['Dx Familienummer'] = udf_data['Dx Familienummer'].split('/')[-1].strip(' ')

        # Set NICU status for related samples using Dx Gerelateerde onderzoeken
        if udf_data['Dx NICU Spoed'] and 'Informativiteitstest' not in udf_data['Dx Onderzoeksreden']:
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

        # Set 'Dx Mengfractie' WES
        if udf_data['Dx Stoftest code'] == config.stoftestcode_wes_duplo:
            udf_data['Dx Mengfractie'] = True

            # Find WES sample(s)
            duplo_samples = lims.get_samples(udf={
                'Dx Persoons ID': udf_data['Dx Persoons ID'],
                'Dx Onderzoeknummer': udf_data['Dx Onderzoeknummer'],
                'Dx Stoftest code': config.stoftestcode_wes,
            })
            if duplo_samples:  # Set duplo status for WES samples
                for duplo_sample in duplo_samples:
                    duplo_sample.udf['Dx Mengfractie'] = True
                    duplo_sample.put()
                    # Check Dx Monsternummer
                    if duplo_sample.udf['Dx Monsternummer'] == udf_data['Dx Monsternummer']:
                        udf_data['Dx Import warning'] = ';'.join([
                            'WES en WES_duplo zelfde monster ({sample}).'.format(sample=duplo_sample.name),
                            udf_data['Dx Import warning']
                        ])
            else:  # Set import warning if no WES samples found
                udf_data['Dx Import warning'] = ';'.join(['Alleen WES_duplo aangemeld.', udf_data['Dx Import warning']])

        elif udf_data['Dx Stoftest code'] == config.stoftestcode_wes:
            # Find WES_duplo sample(s)
            duplo_samples = lims.get_samples(udf={
                'Dx Persoons ID': udf_data['Dx Persoons ID'],
                'Dx Onderzoeknummer': udf_data['Dx Onderzoeknummer'],
                'Dx Stoftest code': config.stoftestcode_wes_duplo,
            })
            if duplo_samples:  # Set duplo status for WES sample
                udf_data['Dx Mengfractie'] = True
                for duplo_sample in duplo_samples:
                    # Remove import warning from WES_duplo samples
                    if (
                        'Dx Import warning' in duplo_sample.udf
                        and 'Alleen WES_duplo aangemeld.' in duplo_sample.udf['Dx Import warning']
                    ):
                        import_warning = duplo_sample.udf['Dx Import warning'].split(';')
                        import_warning.remove('Alleen WES_duplo aangemeld.')
                        duplo_sample.udf['Dx Import warning'] = ';'.join(import_warning)
                        duplo_sample.put()

                    # Check Dx Monsternummer
                    if duplo_sample.udf['Dx Monsternummer'] == udf_data['Dx Monsternummer']:
                        udf_data['Dx Import warning'] = ';'.join([
                            'WES en WES_duplo zelfde monster ({sample}).'.format(sample=duplo_sample.name),
                            udf_data['Dx Import warning']
                        ])
            else:
                udf_data['Dx Mengfractie'] = False

        # Set 'Dx Mengfractie' srWGS
        if udf_data['Dx Stoftest code'] == config.stoftestcode_srwgs_duplo:
            udf_data['Dx Mengfractie'] = True

            # Find srWGS sample(s)
            duplo_samples = lims.get_samples(udf={
                'Dx Persoons ID': udf_data['Dx Persoons ID'],
                'Dx Onderzoeknummer': udf_data['Dx Onderzoeknummer'],
                'Dx Stoftest code': config.stoftestcode_srwgs,
            })
            if duplo_samples:  # Set duplo status for srWGS samples
                for duplo_sample in duplo_samples:
                    duplo_sample.udf['Dx Mengfractie'] = True
                    duplo_sample.put()
                    # Check Dx Monsternummer
                    if duplo_sample.udf['Dx Monsternummer'] == udf_data['Dx Monsternummer']:
                        udf_data['Dx Import warning'] = ';'.join([
                            'srWGS en srWGS_duplo zelfde monster ({sample}).'.format(sample=duplo_sample.name),
                            udf_data['Dx Import warning']
                        ])
            else:  # Set import warning if no srWGS samples found
                udf_data['Dx Import warning'] = ';'.join(['Alleen srWGS_duplo aangemeld.', udf_data['Dx Import warning']])

        elif udf_data['Dx Stoftest code'] == config.stoftestcode_srwgs:
            # Find srWGS_duplo sample(s)
            duplo_samples = lims.get_samples(udf={
                'Dx Persoons ID': udf_data['Dx Persoons ID'],
                'Dx Onderzoeknummer': udf_data['Dx Onderzoeknummer'],
                'Dx Stoftest code': config.stoftestcode_srwgs_duplo,
            })
            if duplo_samples:  # Set duplo status for srWGS sample
                udf_data['Dx Mengfractie'] = True
                for duplo_sample in duplo_samples:
                    # Remove import warning from srWGS_duplo samples
                    if (
                        'Dx Import warning' in duplo_sample.udf
                        and 'Alleen srWGS_duplo aangemeld.' in duplo_sample.udf['Dx Import warning']
                    ):
                        import_warning = duplo_sample.udf['Dx Import warning'].split(';')
                        import_warning.remove('Alleen srWGS_duplo aangemeld.')
                        duplo_sample.udf['Dx Import warning'] = ';'.join(import_warning)
                        duplo_sample.put()

                    # Check Dx Monsternummer
                    if duplo_sample.udf['Dx Monsternummer'] == udf_data['Dx Monsternummer']:
                        udf_data['Dx Import warning'] = ';'.join([
                            'srWGS en srWGS_duplo zelfde monster ({sample}).'.format(sample=duplo_sample.name),
                            udf_data['Dx Import warning']
                        ])
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
                    udf_data['Dx Import warning'] = ';'.join([
                        'Herhaling of dubbele indicatie, beide monsters ingeladen ({sample}).'.format(sample=sample.name),
                        udf_data['Dx Import warning']
                    ])
                elif 'Dx Mengfractie' not in sample.udf or not sample.udf['Dx Mengfractie']:
                    udf_data['Dx Import warning'] = ';'.join([
                        'Eerder onderzoek met protocolomschrijving {protocol} ({sample}).'.format(
                            protocol=sample.udf['Dx Protocolomschrijving'], sample=sample.name
                        ),
                        udf_data['Dx Import warning']
                    ])
            elif (
                sample.udf['Dx Protocolomschrijving'] in udf_data['Dx Protocolomschrijving']
                and sample.udf['Dx Foetus'] == udf_data['Dx Foetus']
            ):
                udf_data['Dx Import warning'] = ';'.join([
                    'Herhaling of dubbele indicatie, beide monsters ingeladen ({sample}).'.format(sample=sample.name),
                    udf_data['Dx Import warning']
                ])

        # Add sample to workflow
        workflow = clarity_epp.upload.utils.stoftestcode_to_workflow(lims, udf_data['Dx Stoftest code'])
        if workflow:
            container = Container.create(lims, type=container_type, name=udf_data['Dx Fractienummer'])
            sample = Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
            lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
            if udf_data['Dx Import warning']:
                sample_messages[sample.name] = "{0}\tCreated and added to workflow: {1}.\tImport warning: {2}".format(
                    sample.name,
                    workflow.name,
                    udf_data['Dx Import warning']
                )
            else:
                sample_messages[sample.name] = "{0}\tCreated and added to workflow: {1}.".format(sample.name, workflow.name)
        else:
            sample_messages[sample_name] += "{0}\tERROR: Stoftest code {1} is not linked to a workflow.".format(
                sample_name,
                udf_data['Dx Stoftest code']
            )

    # Send final email
    message += '\n'.join(sample_messages.values())
    send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)


def from_helix_sql(lims, email_settings, input_file):
    """Upload samples from helix sql 'dna_mons_indi_tijd' export file.

    Args:
        lims (object): Lims connection
        email_settings (dict): Email settings from config file
        input_file (object): File object (read mode)
    """
    filename = input_file.name.rstrip('.csv').split('/')[-1]

    # Try lims connection
    try:
        lims.check_version()
    except ConnectionError:
        subject = f"ERROR Lims Helix Upload: {filename}"
        message = "Kan niet verbinden met de lims server, neem contact op met een lims administrator."
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix_sql'], subject, message)
        sys.exit(message)

    # match header and udf fields
    udf_columns_check = {
        'Dx Persoons ID': {'column': 'Achternaam'},
        'Dx Geboortejaar': {'column': 'Geboortedatum'},
        'Dx GLIMS ID': {'column': 'GLIMS monsternummer'}
    }
    udf_columns_fill = {
        'Dx Geslacht': {'column': 'Geslacht'},
        'Dx Einddatum': {'column': 'Datum aanmelding'},
        'Dx Monsternummer': {'column': 'Monsternummers'},
        'Dx Fractienummer': {'column': 'Fractienummers'},
        'Dx Concentratie (ng/ul)': {'column': 'Conc'},
        'Dx Conc. meting type': {'column': 'Concentratie meting type'},
        'Dx Opslaglocatie': {'column': 'Opslagpositie'},
    }
    for line_index, line in enumerate(input_file):
        if line.startswith('Achternaam'):
            header = line.rstrip().split(';')
            status_column_index = header.index('Status')
            break

    # Setup email
    subject = f"Lims Helix Upload: {filename}"
    message = f"Bestand: {filename}\n\nSamples:\n"
    sample_messages = {}

    for udf_dict in [udf_columns_check, udf_columns_fill]:
        for udf in udf_dict:
            udf_dict[udf]['index'] = header.index(udf_dict[udf]['column'])

    for line_index, line in enumerate(input_file):
        if not line.startswith('.'):
            data = line.rstrip().split(';')
            if data[status_column_index] == 'O':  # only upload status O (opgewerkt) samples
                udf_data = {
                    'Dx Import warning': '',
                    'Dx NICU Spoed': False,
                    'Dx Spoed':	False,
                    'Dx Override Cycles': 'Y150N1;I10N9;I10;Y150N1',
                    'Dx Mergen': False
                }
                for udf in udf_columns_fill:
                    # Transform specific udf
                    try:
                        if udf == 'Dx Geslacht':
                            udf_data[udf] = clarity_epp.upload.utils.transform_sex(data[udf_columns_fill[udf]['index']])
                        elif udf == 'Dx Einddatum':
                            entry_date = datetime.strptime(data[udf_columns_fill[udf]['index']], '%d-%m-%Y')  # Helix format
                            end_date = entry_date + timedelta(weeks=4)
                            udf_data[udf] = end_date.strftime('%Y-%m-%d')  # LIMS format (2021-01-14)
                        elif udf in ['Dx Monsternummer', 'Dx Fractienummer']:
                            udf_data[udf] = clarity_epp.upload.utils.transform_sample_name(
                                data[udf_columns_fill[udf]['index']]
                            )
                        elif udf == 'Dx Concentratie (ng/ul)':
                            udf_data[udf] = data[udf_columns_fill[udf]['index']].replace(',', '.')
                            if udf_data[udf]:
                                udf_data[udf] = float(udf_data[udf])
                        elif udf == 'Dx Conc. meting type':
                            udf_data[udf] = data[udf_columns_fill[udf]['index']].split(' - ')[-1]
                        else:
                            udf_data[udf] = data[udf_columns_fill[udf]['index']]
                    except (IndexError, ValueError):
                        # Catch parsing errors and send email
                        subject = f"ERROR Lims Helix Upload: {filename}"
                        message = (
                            "Kan de data uit het Helix export bestand (sql dna_mons_indi_tijd) niet correct parsen.\n"
                            f"Rij = {line_index+1} \t Kolom = {udf_columns_fill[udf]['column']} \t CF = {udf}.\n"
                            "Check/update het bestand en probeer opnieuw."
                        )
                        send_email(
                            email_settings['server'],
                            email_settings['from'],
                            email_settings['to_import_helix_sql'],
                            subject,
                            message
                        )
                        sys.exit(message)

                # Set 'Dx norm. manueel' udf for concentration and type of measurement
                if udf_data['Dx Concentratie (ng/ul)']:
                    type_of_measurement = udf_data['Dx Conc. meting type']
                    for type_of_measurement, limit in config.manual_normalization_concentration_limits.items():
                        if udf_data['Dx Conc. meting type'] == type_of_measurement:
                            if udf_data['Dx Concentratie (ng/ul)'] <= limit:
                                udf_data['Dx norm. manueel'] = True
                            else:
                                udf_data['Dx norm. manueel'] = False
                else:
                    udf_data['Dx norm. manueel'] = True

                # Set 'Dx Mengfractie' srWGS
                pg_samples = lims.get_samples(udf={
                    'Dx Persoons ID': data[udf_columns_check['Dx Persoons ID']['index']],
                    'Dx Onderzoeksindicatie': 'PG'
                })
                for pg_sample in pg_samples:
                    monster = pg_sample.udf.get('Dx Monsternummer')
                    glims_id = pg_sample.udf.get('Dx GLIMS ID')
                    if not monster and glims_id == line[udf_columns_check['Dx GLIMS ID']['index']]:
                        break
                    elif glims_id != line[udf_columns_check['Dx GLIMS ID']['index']]:
                        udf_data['Dx Mengfractie'] = True
                    else:
                        udf_data['Dx Import warning'] = ';'.join([
                            ('Er is al een PG sample aanwezig in Clarity met hetzelfde Dx Monsternummer '
                            f'({pg_sample.name}, {pg_sample.project.name}).'),
                            udf_data['Dx Import warning']
                        ])

                # Find pg sample in Clarity
                sample_udf = {'Dx Onderzoeksindicatie': 'PG'}
                for udf in udf_columns_check:
                    if udf == 'Dx Geboortejaar':
                        birthday = datetime.strptime(data[udf_columns_check[udf]['index']], '%d-%m-%Y')
                        sample_udf[udf] =  birthday.strftime('%Y')
                    elif udf == 'Dx GLIMS ID':
                        sample_udf[udf] = int(float(data[udf_columns_check[udf]['index']].replace(',', '.')))
                    else:
                        sample_udf[udf] = data[udf_columns_check[udf]['index']]
                sample_name = sample_udf['Dx GLIMS ID']
                samples = lims.get_samples(name=sample_name, udf=sample_udf)

                if not samples:
                    sample_name = udf_data['Dx Monsternummer']
                    glims_id = int(float(data[udf_columns_check[udf]['index']].replace(',', '.')))
                    if udf_data['Dx Import warning']:
                        sample_messages[sample_name] = (
                            f"{sample_name}\tsample {glims_id} niet gevonden in Clarity, niet ingeladen."
                            f"\tImport waarschuwing: {udf_data['Dx Import warning']}"
                        )
                    else:
                        sample_messages[sample_name] = (
                            f"{sample_name}\tsample {glims_id} niet gevonden in Clarity, niet ingeladen."
                        )
                else:
                    for sample in samples:
                        if sample.udf.get('Dx Onderzoeksindicatie') == 'PG':
                            udf_data = {
                                'Dx externe Spoed':	config.external_urgency_pg,
                                'Dx Protocolcode':	config.protocolcode_pg,
                                'Dx Protocolomschrijving':	config.protocoldescription_pg,
                                'Dx Exoomequivalent': config.exoomequivalent_pg,
                                'Dx # clusters/sample': config.clusters_per_sample_pg
                            }
                        # Add sample to workflow
                        workflow = clarity_epp.upload.utils.protocol_description_to_workflow(
                            lims, udf_data['Dx Protocolomschrijving']
                        )
                        if workflow:
                            for udf in udf_data:
                                sample.udf[udf] = udf_data[udf]
                            sample.name = sample.udf['Dx Monsternummer']
                            sample.put()
                            lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
                            if udf_data['Dx Import warning']:
                                sample_messages[sample.name] = (
                                    f"{sample.name}\taangevuld en toegevoegd aan workflow: {workflow.name}."
                                    f"\tImport waarschuwing: {udf_data['Dx Import warning']}"
                                )
                            else:
                                sample_messages[sample.name] = (
                                    f"{sample.name}\taangevuld en toegevoegd aan workflow: {workflow.name}."
                                )
                        else:
                            description = udf_data['Dx Protocolomschrijving']
                            sample_messages[sample_name] = (
                                f"{sample_name}\tERROR: Protocolomschrijving {description} is niet gelinked aan een workflow."
                            )
        else:
            break

    # Send final email
    message += '\n'.join(sample_messages.values())
    send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix_sql'], subject, message)


def from_glims(lims, email_settings, input_file):
    """Upload samples from glims export file.

    Args:
        lims (object): Lims connection
        email_settings (dict): Email settings from config file
        input_file (object): File object (read mode)
    """
    researcher = lims.get_researchers(username="GLIMSCDL")[0]
    filename = input_file.name.rstrip('.csv').split('/')[-1]
    if filename.startswith('Farmacogenetica'):
        filename_date = datetime.strptime(filename[15:23], "%Y%m%d")
        project_name = 'Dx_Farmacogenetica_{date}'.format(date=filename_date.strftime("%Y%m%d"))
    else:
        subject = f"ERROR Lims GLIMS Upload: {filename}"
        message = "Bestandsnaam start niet met Farmacogenetica, project/samples niet aangemaakt."
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_glims'], subject, message)
        sys.exit(message)

    # Try lims connection
    try:
        lims.check_version()
    except ConnectionError:
        subject = f"ERROR Lims GLIMS Upload: {project_name}"
        message = "Kan niet verbinden met de lims server, neem contact op met een lims administrator."
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_glims'], subject, message)
        sys.exit(message)

    # Get or create project
    if not lims.get_projects(name=project_name):
        project = Project.create(lims, name=project_name, researcher=researcher, udf={'Application': 'FG'})
    else:
        project = lims.get_projects(name=project_name)[0]

    container_type = Containertype(lims, id='2')  # Tube

    # match header and udf fields
    udf_column = {
        'Dx Persoons ID': {'column': 'Glims patient id'},
        'Dx GLIMS ID': {'column': 'Glims monster id'},
        'Dx Geboortejaar': {'column': 'geboortejaar'},
        'Dx Onderzoeksindicatie': {'column': 'projectcode'},
    }

    header = input_file.readline().rstrip().split(';') # expect header on first line
    for udf in udf_column:
        udf_column[udf]['index'] = header.index(udf_column[udf]['column'])

    # Setup email
    subject = f"Lims Glims Upload: {project_name}"
    message = f"Project: {project_name}\n\nSamples:\n"
    sample_messages = {}

    # Parse samples
    for line_index, line in enumerate(input_file):
        if ';' in line:
            data = line.rstrip().split(';')

            udf_data = {'Sample Type': 'DNA isolated'}  # required lims input
            for udf in udf_column:
                # Transform specific udf
                try:
                    udf_data[udf] = data[udf_column[udf]['index']]
                except (IndexError, ValueError):
                    # Catch parsing errors and send email
                    subject = f"ERROR Lims Glims Upload: {project_name}"
                    message = (
                        "Kan de data uit het Glims export bestand niet correct parsen.\n"
                        f"Rij = {line_index+1} \t Kolom = {udf_column[udf]['column']} \t CF = {udf}.\n"
                        "Check/update het bestand en probeer opnieuw."
                    )
                    send_email(
                        email_settings['server'], email_settings['from'], email_settings['to_import_glims'], subject, message
                    )
                    sys.exit(message)

            sample_name = f"{udf_data['Dx GLIMS ID']}"

            excisting_clarity_samples = lims.get_samples(
                udf={'Dx GLIMS ID': udf_data['Dx GLIMS ID'], 'Dx Persoons ID': udf_data['Dx Persoons ID']}
            )

            if not excisting_clarity_samples:
                container = Container.create(lims, type=container_type, name=udf_data['Dx GLIMS ID'])
                sample = Sample.create(
                    lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data
                )

                sample_messages[sample.name] = f"{sample.name}\taangemaakt."
            else:
                sample_messages[sample_name] = (
                    f"{sample_name}\tniet aangemaakt, "
                    "er bestaat al een sample in Clarity met dezelfde 'Dx GLIMS ID' en 'Dx Persoons ID'."
                )

    # Send final email
    message += '\n'.join(sample_messages.values())
    send_email(email_settings['server'], email_settings['from'], email_settings['to_import_glims'], subject, message)
