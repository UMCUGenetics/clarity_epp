"""Samplelist functions"""

from genologics.entities import Artifact
import datetime

def removed_samples(lims, output_file):
    """Generates list with samples removed from a workflow and not restarted and where there is no new sample from the same person in a workflow"""
    output_file.write('Datum verwijderd\tOnderzoeks nummer\tOnderzoeks indicatie\tSample\tSample project\tLaatst verwijderd uit stap\tWerklijst nummer\tFouten registratie (oorzaak)\n')
    all_samples = lims.get_samples()
    teller = 0
    restarted = {}
    new_sample = {}
    onderzoeksnummers = {}
    indicaties = {}
    project = {}
    protocol = {}
    wl = {}
    person_samples = {}
    last_removed = {}
    last_removed_stage = {}
    udf = {}
    removed_samples = []
    person_last_process = {}
    sixmonthsago = (datetime.date.today() - datetime.timedelta(6*365/12)).isoformat()

    # 1: Loop through all samples in Clarity LIMS and make list of removed samples and save usefull info of these samples.
    while teller != len(all_samples):
        # 1a: Save usefull info if sample has udf 'Dx Fractienummer'.
        if 'Dx Fractienummer' in all_samples[teller].udf:
            samplename = all_samples[teller].name
            restarted[samplename] = 'NB'
            new_sample[samplename] = 'NB'
            onderzoeksnummers[samplename] = 'NB'
            if 'Dx Onderzoeknummer' in all_samples[teller].udf:
                onderzoeksnummers[samplename] = all_samples[teller].udf['Dx Onderzoeknummer']
            indicaties[samplename] = 'NB'
            if 'Dx Onderzoeksindicatie' in all_samples[teller].udf:
                indicaties[samplename] = all_samples[teller].udf['Dx Onderzoeksindicatie']
            project[samplename] = all_samples[teller].project.name
            if 'Dx Persoons ID' in all_samples[teller].udf:  
                query_udf = {'Dx Persoons ID': all_samples[teller].udf['Dx Persoons ID']}
                samples_person = lims.get_samples(udf=query_udf)
            else:
                samples_person = [all_samples[teller]]
            for person_sample in samples_person:
                if person_sample <> all_samples[teller]:
                    if all_samples[teller].name in person_samples:
                        person_samples[all_samples[teller].name].append(person_sample)
                    else:
                        person_samples[all_samples[teller].name] = [person_sample]
                else:
                    if samplename not in person_samples: 
                        person_samples[samplename] = []
            if 'Dx Protocolomschrijving' in all_samples[teller].udf:
                protocol[samplename] = all_samples[teller].udf['Dx Protocolomschrijving']
            wl[samplename] = 'NB'
            if 'Dx Werklijstnummer' in all_samples[teller].udf:
                wl[samplename] = all_samples[teller].udf['Dx Werklijstnummer']
            artifacts = lims.get_artifacts(type="Analyte", sample_name=all_samples[teller].name)

            # 1b: Add sample to removed samples list if removed and not completed, and determine when last removed.
            for artifact in artifacts:
                statuses = artifact._get_workflow_stages_and_statuses()
                for item in statuses:
                    status = item[1]
                    stage = item[2]
                    if status == 'REMOVED':
                        if artifact.parent_process is not None:
                            proces = artifact.parent_process
                            date = proces.date_run
                            udf[samplename] = 'Niet bekend'
                            if samplename in last_removed:
                                if date >= last_removed[samplename]:
                                    last_removed[samplename] = date
                                    last_removed_stage[samplename] = stage
                                    if 'Dx Fouten registratie (oorzaak)' in proces.udf:
                                        udf[samplename] = proces.udf['Dx Fouten registratie (oorzaak)']
                            else:
                                last_removed[samplename] = date
                                last_removed_stage[samplename] = stage
                                if 'Dx Fouten registratie (oorzaak)' in proces.udf:
                                    udf[samplename] = proces.udf['Dx Fouten registratie (oorzaak)']
                        if all_samples[teller] not in removed_samples:
                            removed_samples.append(all_samples[teller])

            # 1c: Determine if removed sample is restarted after last removal.
            for artifact in artifacts:
                statuses = artifact._get_workflow_stages_and_statuses()
                for item in statuses:
                    status = item[1]
                    if status <> 'REMOVED':
                        if artifact.parent_process is not None:
                            proces = artifact.parent_process
                            date = proces.date_run
                            if samplename in last_removed:
                                if date > last_removed[samplename]:
                                    restarted[samplename] = 'yes'
                                else:
                                    if restarted[samplename] <> 'yes':
                                        restarted[samplename] = 'no'

        teller = teller + 1
        # next sample

    # 2: Loop through all removed samples and determine if there are new samples of the same person.
    for sample in removed_samples:
        samplename = sample.name
        if len(person_samples[samplename]) < 2:
            new_sample[samplename] = 'no'
        else:
            for person_sample in person_samples[samplename]:
                person_last_process[person_sample] = '0000-00-00'
                if 'Dx Protocolomschrijving' in person_sample.udf:
                    if person_sample.udf['Dx Protocolomschrijving'] == protocol[samplename]:
                        if person_sample.date_received > last_removed[samplename]:
                            new_sample[samplename] = 'yes'
                        else:
                            person_artifacts = lims.get_artifacts(type="Analyte", sample_name=person_sample.name)
                            for person_artifact in person_artifacts:
                                if person_artifact.parent_process <> None:
                                    person_proces = person_artifact.parent_process
                                    person_date = person_proces.date_run
                                    if person_date > person_last_process[person_sample]:
                                        person_last_process[person_sample] = person_date
                            if person_last_process[person_sample] > last_removed[samplename]:
                                new_sample[samplename] = 'yes'

    # 3: Loop through removed samples and print in output file if sample is not restarted, when there is no new sample from the same person and the last removed date is in the last 6 months.
    for item in sorted(last_removed.items(), key=lambda x: (x[1], x[0])):
        samplename = item[0]
        if restarted[samplename] <> 'yes' and new_sample[samplename] <> 'yes' and last_removed[samplename] > sixmonthsago:
            output_file.write('{removed}\t{onderzoek}\t{indicatie}\t{name}\t{project}\t{stage}\t{werklijst}\t{udf}\n'.format(
                removed=last_removed[samplename],
                onderzoek=onderzoeksnummers[samplename],
                indicatie=indicaties[samplename],
                name=samplename,
                project=project[samplename],
                stage=last_removed_stage[samplename],
                werklijst=wl[samplename],
                udf=udf[samplename]
            ))

    output_file.write('---\t---\t---\teinde lijst\t---\t---\t---\t---')
