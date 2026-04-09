"""Barcode  placement functions."""
import sys

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


def get_reagent_category_for_artifact(lims, artifact):
    """Gets the reagent category name of the reagent type/label of the given artifact object.

    Args:
        lims (object): Lims connection
        artifact (object): Lims Artifact object

    Returns:
        str: Reagent category name
    """
    reagent_label = artifact.reagent_labels[0]
    reagent_type = lims.get_reagent_types(name=reagent_label)[0]
    reagent_category = reagent_type.category
    return reagent_category


def check_plate_id_with_used_reagent_labels(lims, process):
    """Performs check: Plate number in process udf "Twist barcode plaat ID" is the same as plate number in the reagent category
    of the added reagent labels in this process.

    Args:
        lims (object): Lims connection
        process (object): Lims Process object
    """
    twist_plate = process.udf["Twist barcode plaat ID"]
    for artifact in process.analytes()[0]:
        reagent_category = get_reagent_category_for_artifact(lims, artifact)
        if twist_plate not in reagent_category:
            message = ("Index adapater platen komen niet overeen")
            sys.exit(message)
