"""Sample upload epp functions."""
import re
import sys
from datetime import datetime

from genologics.entities import Container, Containertype, Project, Sample
from requests.exceptions import ConnectionError

import clarity_epp.upload.utils
import config

from .. import send_email


def from_helix(lims, email_settings, input_file):
    """Upload samples from helix export file."""
    project_name = f"Dx {input_file.name.rstrip('.csv').split('/')[-1]}"
    helix_initials = project_name.split('_')[-1]

    # Try lims connection
    try:
        lims.check_version()
    except ConnectionError:
        subject = f"ERROR Lims Helix Upload: {project_name}"
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
        subject = f"ERROR Lims Helix Upload: {project_name}"
        message = f"Can't find researcher with initials: {helix_initials}."
        send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
        sys.exit(message)

    # Create project
    if not lims.get_projects(name=project_name):
        project = Project.create(lims, name=project_name, researcher=researcher, udf={'Application': 'DX'})
    else:
        subject = f"ERROR Lims Helix Upload: {project_name}"
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
        'Dx gerelateerde oz #': {'column': 'Aantal gerelateerde onderzoeken'},
        'Dx Conc. meting type': {'column': 'Concentratie meting type'},
        'Dx RIN/DIN waarde': {'column': 'RIN/DIN'},
    }
    header = input_file.readline().rstrip().rstrip('.').split(',') # expect header on first line
    for udf in udf_column.keys():
        udf_column[udf]['index'] = header.index(udf_column[udf]['column'])

    # Setup email
    subject = f"Lims Helix Upload: {project_name}"
    message = f"Project: {project_name}\n\nSamples:\n"
    sample_messages = {}

    # Parse samples
    for line_index, line in enumerate(input_file):
        data = line.rstrip().split('","')
        for i in [0, -1]:  # instead of .strip('"') in line above, because that doesn't work if last column is empty ("")
            data[i] = data[i].replace('"', '')

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
                elif udf in ['Dx Concentratie (ng/ul)', 'Dx RIN/DIN waarde']:
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
                subject = f"ERROR Lims Helix Upload: {project_name}"
                message = (
                    "Could not correctly parse data from helix export file (werklijst).\n"
                    f"Row = {line_index+1} \t Column = {udf_column[udf]['column']} \t UDF = {udf}.\n"
                    "Please check/update the file and try again. Make sure to remove the project from LIMS before retrying."
                )
                send_email(
                    email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message
                )
                sys.exit(message)

        sample_name = f"{udf_data['Dx Monsternummer']}_{udf_data['Dx Meet ID']}"

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

        # Set 'Dx Familie status' udf
        if('Bevestiging diagnose' in udf_data['Dx Onderzoeksreden']
                or 'Prenataal onderzoek' in udf_data['Dx Onderzoeksreden']
                or 'Eerstegraads-verwantenond' in udf_data['Dx Onderzoeksreden']
                or 'Partneronderzoek' in udf_data['Dx Onderzoeksreden']
                or 'Dragerschapbepaling' in udf_data['Dx Onderzoeksreden']
                or 'Presymptomatisch onderzoe' in udf_data['Dx Onderzoeksreden']): # Helix export is truncated (onderzoek)
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
                f"Meerdere familienummers, laatste wordt gebruikt. ({udf_data['Dx Familienummer']})",
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

        # Set 'Dx Mengfractie' WES (do not transfer this if/elif for stoftestcode_wes(_duplo) to v2, not used anymore)
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
                            f'WES en WES_duplo zelfde monster ({duplo_sample.name}).',
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
                            f'WES en WES_duplo zelfde monster ({duplo_sample.name}).',
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
                            f'srWGS en srWGS_duplo zelfde monster ({duplo_sample.name}).',
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
                            f'srWGS en srWGS_duplo zelfde monster ({duplo_sample.name}).',
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
                        f'Herhaling of dubbele indicatie, beide monsters ingeladen ({sample.name}).',
                        udf_data['Dx Import warning']
                    ])
            elif (
                sample.udf['Dx Protocolomschrijving'] in udf_data['Dx Protocolomschrijving']
                and sample.udf['Dx Foetus'] == udf_data['Dx Foetus']
            ):
                udf_data['Dx Import warning'] = ';'.join([
                    f"Herhaling of dubbele indicatie, beide monsters ingeladen ({sample.name}).",
                    udf_data['Dx Import warning']
                ])

        # Add sample to workflow
        workflow = clarity_epp.upload.utils.stoftestcode_to_workflow(lims, udf_data['Dx Stoftest code'])
        if workflow:
            container = Container.create(lims, type=container_type, name=udf_data['Dx Fractienummer'])
            sample = Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
            lims.route_artifacts([sample.artifact], workflow_uri=workflow.uri)
            if udf_data['Dx Import warning']:
                sample_messages[sample.name] = (
                    f"{sample.name}\tCreated and added to workflow: {workflow.name}."
                    f"\tImport warning: {udf_data['Dx Import warning']}"
                )
            else:
                sample_messages[sample.name] = f"{sample.name}\tCreated and added to workflow: {workflow.name}."
        else:
            sample_messages[sample_name] += (
                f"{sample_name}\tERROR: Stoftest code {udf_data['Dx Stoftest code']} is not linked to a workflow."
            )

    # Send final email
    message += '\n'.join(sample_messages.values())
    send_email(email_settings['server'], email_settings['from'], email_settings['to_import_helix'], subject, message)
