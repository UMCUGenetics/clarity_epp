"""Sample export functions."""
import datetime

import clarity_epp.export.utils


def removed_samples(lims, output_file):
    """Export table with samples that are removed from a workflow."""
    output_file.write('Datum verwijderd\tSample\tSample project\tWerklijst\tOnderzoeks nummer\tOnderzoeks indicatie\tVerwijderd uit stap\tStatus\n')

    # Get DX samples
    dx_projects = lims.get_projects(udf={'Application': 'DX'})
    dx_samples = []

    for project in dx_projects:
        dx_samples.extend(lims.get_samples(projectname=project.name))

    for sample in dx_samples:
        sample_removed = False
        removed_stage = None
        removed_process_id = None
        removed_date = None

        for artifact in sorted(lims.get_artifacts(type="Analyte", sample_name=sample.name, resolve=True), key=clarity_epp.export.utils.sort_artifact_list):
            for stage, status, name in artifact.workflow_stages_and_statuses:
                if status == 'REMOVED':  # Store removed from workflow
                    sample_removed = True
                    removed_stage = stage

                    # Find removed process
                    processes = list(set(lims.get_processes(inputartifactlimsid=artifact.id, type=name)))
                    if processes:
                        removed_process_id = int(processes[0].id.split('-')[1])  # Use the first one
                        removed_date = datetime.datetime.strptime(processes[0].date_run, '%Y-%m-%d')  # Use the first one

                    # Removed process not found use parent process
                    elif artifact.parent_process:
                        removed_process_id = int(artifact.parent_process.id.split('-')[1])
                        removed_date = datetime.datetime.strptime(artifact.parent_process.date_run, '%Y-%m-%d')

                    # Samples uploaded and removed from workflow without any work done.
                    else:
                        removed_process_id = 0
                        removed_date = datetime.datetime.strptime(sample.date_received, '%Y-%m-%d')

                elif sample_removed and status == 'COMPLETE':
                    # Same process/stage completed after removal.
                    if stage == removed_stage:
                        sample_removed = False
                        removed_stage = None
                        removed_process_id = None
                        removed_date = None

                    # Other process completed.
                    else:
                        processes = list(set(lims.get_processes(inputartifactlimsid=artifact.id, type=name)))
                        if artifact.parent_process:
                            processes.append(artifact.parent_process)  # Also check parent_process
                        for process in processes:
                            process_id = int(process.id.split('-')[1])

                            if process_id > removed_process_id:  # Other process completed after removal from workflow
                                sample_removed = False
                                removed_stage = None
                                removed_process_id = None
                                removed_date = None
                                break

        # Check other samples from same person
        if sample_removed:
            person_samples = lims.get_samples(udf={
                'Dx Persoons ID': sample.udf['Dx Persoons ID'],
                'Dx Geslacht': sample.udf['Dx Geslacht'],
                'Dx Familie status': sample.udf['Dx Familie status'],
            })
            for person_sample in person_samples:
                if person_sample.id != sample.id and sample_removed:
                    person_sample_date = datetime.datetime.strptime(person_sample.date_received, '%Y-%m-%d')
                    if person_sample_date > removed_date:  # New sample loaded after removal from workflow
                        sample_removed = False
                        removed_stage = None
                        removed_process_id = None
                        removed_date = None

                    else:  # Work done on other sample after removal from workflow
                        for artifact in lims.get_artifacts(type="Analyte", sample_name=person_sample.name, resolve=True):
                            for stage, status, name in artifact.workflow_stages_and_statuses:
                                if status == 'COMPLETE':
                                    processes = list(set(lims.get_processes(inputartifactlimsid=artifact.id, type=name)))
                                    if artifact.parent_process:
                                        processes.append(artifact.parent_process)  # Also check parent_process
                                    for process in processes:
                                        process_id = int(process.id.split('-')[1])
                                        if process_id > removed_process_id:  # Other process completed after removal from workflow
                                            sample_removed = False
                                            removed_stage = None
                                            removed_process_id = None
                                            removed_date = None
                                            break

                            if not sample_removed:
                                break

        if sample_removed:
            sample_removed_status = ''
            if 'Dx sample status verwijderd' in sample.udf:
                sample_removed_status = sample.udf['Dx sample status verwijderd']

            elapsed_time = datetime.datetime.now() - removed_date

            # Filter samples on sample_removed_status and elapsed month (6 => 6*31 = 186 days) since removal.
            if (not sample_removed_status or sample_removed_status == 'Nieuw materiaal aangevraagd') and elapsed_time.days < 186:
                output_file.write('{removed_date}\t{name}\t{project}\t{werklijst}\t{onderzoek}\t{indicatie}\t{stage}\t{removed_status}\n'.format(
                    removed_date=removed_date.strftime('%Y-%m-%d'),
                    name=sample.name,
                    project=sample.project.name,
                    werklijst=sample.udf['Dx Werklijstnummer'],
                    onderzoek=sample.udf['Dx Onderzoeknummer'],
                    indicatie=sample.udf['Dx Onderzoeksindicatie'],
                    stage=removed_stage.name,
                    removed_status=sample_removed_status
                ))


def sample_indications(lims, output_file, artifact_name=None, sequencing_run=None, sequencing_run_project=None):
    """Export table with sample indications. Lookup samples by sample name or sequencing run (project)."""
    samples = []

    # Get samples by artifact_name
    if artifact_name:
        artifacts = lims.get_artifacts(name=artifact_name)
        samples = {artifact_name: artifact.samples[0] for artifact in artifacts}

    # Get samples by sequencing run
    elif sequencing_run:
        udf_query = {'Dx Sequencing Run ID': sequencing_run}
        if sequencing_run_project:
            udf_query['Dx Sequencing Run Project'] = sequencing_run_project

        artifacts = lims.get_artifacts(type='Analyte', udf=udf_query)
        samples = {artifact.name: artifact.samples[0] for artifact in artifacts}

    # Write result
    if samples:
        output_file.write('Sample\tIndication\n')
        for sample_name, sample in samples.items():
            output_file.write(
                '{sample}\t{indication}\n'.format(
                    sample=sample_name,
                    indication=sample.udf['Dx Onderzoeksindicatie'].split(';')[0]  # select newest indication
                )
            )
    else:
        print("no_sample_found")
