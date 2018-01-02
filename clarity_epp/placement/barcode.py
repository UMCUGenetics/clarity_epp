"""Barcode  placement functions."""

from genologics.entities import Process


def check_family(lims, process_id):
    """Check barcodes."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        sample = artifact.samples[0]
        barcode = artifact.reagent_labels[0]

        query_udf = {'Dx Familienummer': sample.udf['Dx Familienummer']}

        family_samples = lims.get_samples(udf=query_udf)
        for family_sample in family_samples:
            if family_sample.id != sample.id:
                family_sample_artifacts = lims.get_artifacts(samplelimsid=family_sample.id, reagent_label=barcode, process_type=process.type.name)
                if family_sample_artifacts:
                    artifact.udf['Dx monster met BC duplicaat'] = "{sample}".format(sample=family_sample.name)
                    artifact.put()
