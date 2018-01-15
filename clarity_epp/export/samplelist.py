"""Samplelist functions"""

from genologics.entities import Artifact

def removed_samples(lims, output_file):
    """Generates list with samples removed frow a workflow and where there is no new sample from the same person in a workflow"""
    output_file.write('Datum ingeladen\tOnderzoeksnummer\tHelix indicatie\tSample\tVerwijderd uit stadia\n')
    all_samples = lims.get_samples()
    teller = 0
    removed_samples_stage = {}
    removed_samples_received = {}
    removed_samples_indicatie = {}
    removed_samples_onderzoeksnummer = {}
    while teller != len(all_samples):
        sample = all_samples[teller].name
        received = 'NB'
        indicatie = 'NB'
        onderzoeksnummer = 'NB'
        if 'Dx Tecan std' not in sample:
            if '2' == sample[:1] or 'D' == sample[:1]:
                artifacts = lims.get_artifacts(type="Analyte", sample_name=all_samples[teller].name)
                status_dic = {}
                for artifact in artifacts:
                    status = artifact._get_workflow_stages_and_statuses()
                    for stage in status:
                        s = stage[1]
                        s2 = stage[2]
                        if s in status_dic:
                            status_dic[s].append(s2)
                        else:
                            status_dic[s] = [s2]
                received = all_samples[teller].date_received
                if 'Dx Onderzoeksindicatie' in all_samples[teller].udf:
                    indicatie = all_samples[teller].udf['Dx Onderzoeksindicatie']
                if 'Dx Onderzoeknummer' in all_samples[teller].udf:
                    onderzoeksnummer = all_samples[teller].udf['Dx Onderzoeknummer']
                if 'REMOVED' in status_dic:
                    removed_samples_stage[sample] = status_dic['REMOVED']
                    removed_samples_received[sample] = received
                    removed_samples_indicatie[sample] = indicatie
                    removed_samples_onderzoeksnummer[sample] = onderzoeksnummer
        teller = teller + 1
    for item in sorted(removed_samples_received.items(), key=lambda x: (x[1], x[0])):
        sample = item[0]
        output_file.write('{received}\t{onderzoeksnummer}\t{indicatie}\t{sample}\t{stages}\n'.format(
            received=removed_samples_received[sample],
            onderzoeksnummer=removed_samples_onderzoeksnummer[sample],
            indicatie=removed_samples_indicatie[sample],
            sample=sample,
            stages=removed_samples_stage[sample]
        ))
