"""Sample export functions."""
import datetime

from genologics.entities import Process

import clarity_epp.export.utils


def removed_samples(lims, output_file):
    """Export table with samples that are removed from a workflow."""
    output_file.write('Datum verwijderd\tSample\tSample project\tWerklijst\tOnderzoeks nummer\tOnderzoeks indicatie\tVerwijderd uit stap\tStatus\n')

    # Get DX samples
    dx_projects = lims.get_projects(udf={'Application': 'DX'})
    dx_samples = []

    for project in dx_projects:
        samples = lims.get_samples(projectname=project.name)
        for sample in samples:
            # only include with date_received < 1 year
            date_received = datetime.datetime.strptime(sample.date_received, '%Y-%m-%d')
            if date_received > datetime.datetime.now() - datetime.timedelta(days=365):
                dx_samples.append(sample)

    for sample in dx_samples:
        sample_removed = False
        removed_stage = None
        removed_process_id = 0
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
                        removed_process_id = 0
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
                                removed_process_id = 0
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
                        removed_process_id = 0
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
                                            removed_process_id = 0
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


def get_artifact_samples(lims, artifact_name=None, sequencing_run=None, sequencing_run_project=None):
    """Lookup samples by artifact name or sequencing run (project)."""
    samples = {}

    # Get samples by artifact_name
    if artifact_name:
        samples[artifact_name] = set()
        artifacts = lims.get_artifacts(name=artifact_name)
        for artifact in artifacts:
            samples[artifact_name].add(artifact.samples[0])

    # Get samples by sequencing run
    elif sequencing_run:
        udf_query = {'Dx Sequencing Run ID': sequencing_run}
        if sequencing_run_project:
            udf_query['Dx Sequencing Run Project'] = sequencing_run_project

        artifacts = lims.get_artifacts(type='Analyte', udf=udf_query)
        for artifact in artifacts:
            if artifact.name not in samples:
                samples[artifact.name] = set()
            samples[artifact.name].add(artifact.samples[0])

    return samples


def sample_udf_dx(lims, output_file, artifact_name=None, sequencing_run=None, sequencing_run_project=None, udf=None, column_name=None):
    """Export table with sample udf (Dx-udf only)."""
    artifact_samples = get_artifact_samples(lims, artifact_name, sequencing_run, sequencing_run_project)

    # Write result
    if artifact_samples:
        output_file.write(f'Sample\t{column_name}\n')
        for artifact_name, samples in artifact_samples.items():
            sample_udf_values= set()
            for sample in samples:
                if udf in sample.udf:
                    if type(sample.udf[udf]) is str:
                        udf_value=sample.udf[udf].split(';')[0]  # select newest udf value
                    else:
                        udf_value=sample.udf[udf]
                    sample_udf_values.add(udf_value)

            if len(sample_udf_values) == 1:
                output_file.write('{sample}\t{udf_value}\n'.format(sample=artifact_name, udf_value=udf_value))
            elif len(sample_udf_values) > 1:
                output_file.write('{sample}\t{udf_value}\n'.format(sample=artifact_name, udf_value='multiple_values_for_udf'))
            else:
                output_file.write('{sample}\t{udf_value}\n'.format(sample=artifact_name, udf_value='unknown'))
    else:
        print("no_sample_found")


def sample_related_mip(lims, process_id, output_file):
    """Export related mip samples for all samples in process."""
    process = Process(lims, id=process_id)

    # Create output item per artifact
    output = []
    for artifact in process.all_inputs():
        if 'Dx mip' in artifact.samples[0].udf:
            output.append('{sample},{related_mip}'.format(
                sample=artifact.name,
                related_mip=artifact.samples[0].udf['Dx mip']
            ))

    # Print output items, last line only contains a line end to work with fingerprintDB.
    output_file.write(',\n'.join(output))
    output_file.write('\n')
