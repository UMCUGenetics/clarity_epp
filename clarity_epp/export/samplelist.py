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
    removed_samples_protocol = {}
    removed_samples_new_sample = {}
    new_samples_received = {}
    new_samples_protocol = {}
    new_samples_name = {}

    while teller != len(all_samples):
        samplename = all_samples[teller].name
        received = 'NB'
        indicatie = 'NB'
        onderzoeksnummer = 'NB'
        protocol = 'NB'
        if 'Dx Tecan std' not in samplename:
            if '2' == samplename[:1] or 'D' == samplename[:1]:
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
                if 'Dx Protocolomschrijving' in all_samples[teller].udf:
                    protocol = all_samples[teller].udf['Dx Protocolomschrijving']
                if 'REMOVED' in status_dic:
                    sample = all_samples[teller]
                    if 'Dx Persoons ID' in sample.udf:
                        query_udf = {'Dx Persoons ID': sample.udf['Dx Persoons ID']}
                        person_samples = lims.get_samples(udf=query_udf)
                    else:
                        person_samples = []
                    new_sample = 'NB'
                    if len(person_samples) < 2:
                        new_sample = 'nee'
                        removed_samples_stage[samplename] = status_dic['REMOVED']
                        removed_samples_received[samplename] = received
                        removed_samples_indicatie[samplename] = indicatie
                        removed_samples_onderzoeksnummer[samplename] = onderzoeksnummer
                        removed_samples_protocol[samplename] = protocol
                        removed_samples_new_sample[samplename] = new_sample
                        new_samples_received[samplename] = ''
                        new_samples_protocol[samplename] = ''
                    else:
                        for person_sample in person_samples:
                            if person_sample.date_received > all_samples[teller].date_received:
                                new_sample = 'ja'
                                if samplename in new_samples_received:
                                    new_samples_received[samplename].append(person_sample.date_received)
                                    if 'Dx Protocolomschrijving' in person_sample.udf:
                                        new_samples_protocol[samplename].append(person_sample.udf['Dx Protocolomschrijving'])
                                    else:
                                        new_samples_protocol[samplename].append('NB')
                                else:
                                    new_samples_received[samplename] = [person_sample.date_received]
                                    if 'Dx Protocolomschrijving' in person_sample.udf:
                                        new_samples_protocol[samplename] = [person_sample.udf['Dx Protocolomschrijving']]
                                    else:
                                        new_samples_protocol[samplename] = ['NB']
                            removed_samples_stage[samplename] = status_dic['REMOVED']
                            removed_samples_received[samplename] = received
                            removed_samples_indicatie[samplename] = indicatie
                            removed_samples_onderzoeksnummer[samplename] = onderzoeksnummer
                            removed_samples_protocol[samplename] = protocol
                            removed_samples_new_sample[samplename] = new_sample
                        if new_sample <> 'ja':
                            new_samples_received[samplename] = ''
                            new_samples_protocol[samplename] = ''
        teller = teller + 1

    for item in sorted(removed_samples_received.items(), key=lambda x: (x[1], x[0])):
        sample = item[0]
        if removed_samples_new_sample[sample] <> 'ja' or removed_samples_protocol[sample] not in new_samples_protocol[sample]:
            output_file.write('{received}\t{onderzoeksnummer}\t{indicatie}\t{sample}\t{stages}\n'.format(
                received=removed_samples_received[sample],
                onderzoeksnummer=removed_samples_onderzoeksnummer[sample],
                indicatie=removed_samples_indicatie[sample],
                sample=sample,
                stages=removed_samples_stage[sample]
            ))
