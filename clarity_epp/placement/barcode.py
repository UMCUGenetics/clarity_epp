"""Barcode  placement functions."""

from genologics.entities import Process


def check_family(lims, process_id):
    """Check barcodes."""
    process = Process(lims, id=process_id)
    for artifact in process.analytes()[0]:
        sample = artifact.samples[0]
        barcode = artifact.reagent_labels[0]

        try:
            query_udf = {'Dx Familienummer': sample.udf['Dx Familienummer']}
        except KeyError:
            artifact.udf['Dx monster met BC duplicaat'] = "Barcode niet gecontroleerd."
            artifact.put()
        else:
            family_samples = lims.get_samples(udf=query_udf)
            for family_sample in family_samples:
                if family_sample.id != sample.id and family_sample.udf['Dx Persoons ID'] != sample.udf['Dx Persoons ID']:
                    family_sample_artifacts = lims.get_artifacts(samplelimsid=family_sample.id, reagent_label=barcode, process_type=process.type.name)
                    if family_sample_artifacts:
                        artifact.udf['Dx monster met BC duplicaat'] = "{sample}".format(sample=family_sample.name)
                        artifact.put()
