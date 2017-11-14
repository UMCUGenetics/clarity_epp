"""Samplenames functions."""

from genologics.entities import Process
import datetime

def family_status(lims, process_id):
    """Generates family status for user check"""
    process = Process(lims, id=process_id)
    years = {}
    births_per_family = {}
    status = {}
    all_samples_Unummer = []

    for artifact in process.all_outputs():
        Unummer = artifact.samples[0].udf['Dx Unummer']
        if Unummer not in all_samples_Unummer:
            query_udf = {'Dx Unummer': Unummer}
            family_samples = lims.get_samples(udf=query_udf)
            for family_sample in family_samples:
                monsternummer = family_sample.name
                years[monsternummer] = family_sample.udf['Dx Geboortejaar']
                if family_sample.udf['Dx Foetus'] == True:
                    years[monsternummer] = datetime.datetime.now().year
                if Unummer in births_per_family:
                    births_per_family[Unummer].append(years[monsternummer])
                else:
                    births_per_family[Unummer] = [years[monsternummer]]
            all_samples_Unummer.append(Unummer) 

    for artifact in process.all_outputs():
        monsternummer = artifact.samples[0].name
        Unummer = artifact.samples[0].udf['Dx Unummer']
        if len(births_per_family[Unummer]) == 1:
            status[monsternummer] = 'Child'
        elif len(births_per_family[Unummer]) == 3:
            if years[monsternummer] == max(births_per_family[Unummer]):
                status[monsternummer] = 'Child'
            elif years[monsternummer] < (max(births_per_family[Unummer]) - 13):
                status[monsternummer] = 'Parent'
            else:
                status[monsternummer] = 'Child'
        else:
            status[monsternummer] = 'Unknown'

    for artifact in process.all_outputs():
        monsternummer = artifact.samples[0].name
        artifact.udf['Dx Familie status'] = "{status}".format(status=status[monsternummer])
        artifact.put()
