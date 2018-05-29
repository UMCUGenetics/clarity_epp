"""Samplelist functioins"""

from genologics.entities import Artifact

def removed_samples(lims, output_file):
    """Generates list with samples removed frow a workflow and not restarted and where there is no new sample from the same person in a workflow"""
    output_file.write('Datum verwijderd\tOnderzoeks nummer\tOnderzoeks indicatie\tSample\tSample project\tLaatst verwijderd uit stap\n')
    all_samples = lims.get_samples()
    teller = 0
    restarted = {}
    new_sample = {}
    onderzoeksnummers = {}
    indicaties = {}
    project = {}
    protocol = {}
    person_samples = {}
    last_removed = {}
    last_removed_stage = {}
    removed_samples = []
    person_last_process = {}

    while teller != len(all_samples):
        if 'Dx Fractienummer' in all_samples[teller].udf:
            samplename = all_samples[teller].name
            completed = all_samples[teller].date_completed
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
                samples_person = []
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
            artifacts = lims.get_artifacts(type="Analyte", sample_name=all_samples[teller].name)

            for artifact in artifacts:
                statuses = artifact._get_workflow_stages_and_statuses()
                for item in statuses:
                    status = item[1]
                    stage = item[2]
                    if status == 'REMOVED':
                        if completed is None:
                            if artifact.parent_process is not None:
                                proces = artifact.parent_process
                                date = proces.date_run
                                if samplename in last_removed:
                                    if date > last_removed[samplename]:
                                        last_removed[samplename] = date
                                        last_removed_stage[samplename] = stage
                                else:
                                    last_removed[samplename] = date
                                    last_removed_stage[samplename] = stage
                            if all_samples[teller] not in removed_samples:
                                removed_samples.append(all_samples[teller])

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

    for item in sorted(last_removed.items(), key=lambda x: (x[1], x[0])):
        samplename = item[0]
        if restarted[samplename] <> 'yes' and new_sample[samplename] <> 'yes':
            output_file.write('{removed}\t{onderzoek}\t{indicatie}\t{name}\t{project}\t{stage}\n'.format(
                removed=last_removed[samplename],
                onderzoek=onderzoeksnummers[samplename],
                indicatie=indicaties[samplename],
                name=samplename,
                project=project[samplename],
                stage=last_removed_stage[samplename]
            ))

    output_file.write('---\t---\t---\teinde lijst\t---\t---')
