from collections import OrderedDict
import re

from genologics.lims import Lims
from genologics.entities import Artifact, SampleHistory, Protocol

# Setup lims connection
baseuri = 'https://usf-lims.umcutrecht.nl'
username = 'lims_user'
password = 'lims_user_password'
lims = Lims(baseuri, username, password)

# Get DX projects and filter on year based on project name
dx_projects = [project for project in lims.get_projects(udf={'Application': 'DX'}) if project.name.startswith('Dx WL20')]
sample_count = 0

# Expected actions
action_list = ['total', 'complete', 'nextstep', 'remove', 'rework', 'repeat', 'completerepeat', 'store', 'leave', 'None']

# Expected processes
processes = [
    'Dx Sample registratie zuivering', 'Dx Hamilton uitvullen', 'Dx Hamilton zuiveren',
    'Dx Zuiveren gDNA manueel', 'Dx manueel gezuiverd placement', 'Dx gDNA Normalisatie Caliper', 'Dx Fragmenteren & BBSS',
    'Dx LibraryPrep Caliper KAPA', 'Dx Library Prep amplificatie & clean up KAPA', 'Dx Multiplexen library prep',
    'Dx Enrichment DNA fragments', 'Dx Post Enrichment clean up', 'Dx Aliquot Post Enrichment (clean)',
    'Dx Post Enrichment PCR & clean up', 'Dx Aliquot Post Enrichment PCR (clean)',
    'Dx Library pool verdunnen', 'Dx Multiplexen library pool', 'Dx Multiplexen sequence pool',
    'Dx Library pool denatureren en laden (NovaSeq)', 'Dx Automated NovaSeq Run (standaard)',
    'Dx Library pool denatureren en laden (Nextseq)', 'Dx NextSeq Run',
    'Dx Library pool denatureren en laden (NovaSeq) Dx QC controle Lab sequencen',
    'Dx Library pool denatureren en laden (Nextseq) Dx QC controle Lab sequencen',
    'Dx NGS labwerk afronden', 'Dx Bioinformatica analyses', 'Dx NGS onderzoeken afronden',
]

# Append combined process name for qc processes
qc_processes = [
    'Dx Qubit QC', 'Dx Tecan Spark 10M QC', 'Dx Bioanalyzer QC',
    'Dx Tapestation 2200 QC', 'Dx Tapestation 4200 QC', 'Dx Aggregate QC'
]
processes_before_qc = [
    'Dx Hamilton zuiveren', 'Dx Zuiveren gDNA manueel', 'Dx Fragmenteren & BBSS', 'Dx LibraryPrep Caliper KAPA',
    'Dx Library Prep amplificatie & clean up KAPA', 'Dx Post Enrichment PCR & clean up', 'Dx Multiplexen library pool'
]
for process in processes_before_qc:
    for qc_process in qc_processes:
        processes.append("{0} {1}".format(process, qc_process))
processes.extend(qc_processes)

# Setup count dictonary
process_action_counts = OrderedDict()
for process in processes:
    process_action_counts[process] = {}
    for action in action_list:
        process_action_counts[process][action] = 0

for project in dx_projects:
    for sample in lims.get_samples(projectlimsid=project.id):
        if sample.udf['Dx Onderzoeksreden'] == 'Research':  # skip research
            continue
        sample_count += 1
        for artifact in lims.get_artifacts(samplelimsid=sample.id, resolve=True, type='Analyte'):
            for process in lims.get_processes(inputartifactlimsid=artifact.id):

                # Parse process name, remov version. Add to count dictonary if not yet defined.
                process_name = re.sub(r' v\d\.\d', '', process.type.name)
                if 'QC' in process_name and artifact.parent_process:
                    process_name = "{0} {1}".format(re.sub(r' v\d\.\d', '', artifact.parent_process.type.name), process_name)

                # Find output artifacts
                output_artifacts = []
                if process.all_outputs():  # outputs_per_input returns TypeError if there is no output
                    output_artifacts = [output_artifact.id for output_artifact in process.outputs_per_input(artifact.id, Analyte=True)]

                # For 'Bioinformatica analyses' and 'NGS onderzoeken afronden' we need to demux to get correct artifact
                if process_name in ['Dx Bioinformatica analyses', 'Dx NGS onderzoeken afronden']:
                    artifact_demux = lims.get('/demux?'.join(artifact.uri.split('?')))
                    for node in artifact_demux.getiterator('artifact'):
                        if node.find('samples') and len(node.find('samples').findall('sample')) == 1:
                            demux_artifact = Artifact(lims, uri=node.attrib['uri'])
                            if sample == demux_artifact.samples[0]:  # 1 sample per artifact.
                                output_artifacts = [demux_artifact.id]
                                break

                # Some processes do not create an output artifcat (mainly QC)
                if not output_artifacts:
                    output_artifacts = [artifact.id]

                # Get action for artifact
                for action in process.step.actions.get_next_actions():
                    if action['artifact'].id in output_artifacts:
                        process_action_counts[process_name]['total'] += 1
                        process_action_counts[process_name][str(action['action'])] += 1

print 'Total Sample count: {0}'.format(str(sample_count))
print 'Process\t{action_list}'.format(action_list='\t'.join(action_list))
for process in process_action_counts:
    if process_action_counts[process]['total']:
        print '{process}\t{action_list}'.format(
            process=process,
            action_list='\t'.join([str(process_action_counts[process][action]) if action in process_action_counts[process] else '0' for action in action_list])
        )
