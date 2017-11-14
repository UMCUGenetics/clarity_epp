"""Barcode  placement functions."""

from genologics.entities import Process


def check_family(lims, process_id):
    """Check barcodes."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        sample = artifact.samples[0]
        barcode = artifact.reagent_labels[0]

        query_udf = {'Dx Unummer': sample.udf['Dx Unummer']}

        family_samples = lims.get_samples(udf=query_udf)
        for family_sample in family_samples:
            if family_sample.id != sample.id:
                family_sample_artifacts = lims.get_artifacts(samplelimsid=family_sample.id, reagent_label=barcode, process_type=process.type.name)
                if family_sample_artifacts:
                    artifact.udf['Dx monster met BC duplicaat'] = "{sample}".format(sample=family_sample.name)
                    artifact.put()


def check_pool(lims, process_id):
    """Check for duplicate barcodes in pools."""
    process = Process(lims, id=process_id)
    for container in process.output_containers():
        artifact = container.placements['1:1']
        pool = artifact.name
        barcodes = {}
        barcodes[pool] = [artifact.reagent_labels]
        if len(barcodes) != len(set(barcodes)):
            artifact.udf['Dx pool met BC duplicaat'] = "{pool}".format(pool="BC duplicaat in deze pool")
            artifact.put()
