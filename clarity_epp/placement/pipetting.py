"""Pipetting  placement functions."""

from genologics.entities import Process

from .. import get_mix_sample_barcode


def check_nunc_input_nunc_output(lims, process_id):
    """Check nuncs."""
    process = Process(lims, id=process_id)
    for output_artifact in process.all_outputs():
        if output_artifact.type == 'Analyte':
            input_nunc_1 = ''
            input_nunc_2 = ''
            output_nunc = ''
            sample_mix = False
            if len(output_artifact.samples) > 1:
                sample_mix = True
                mix_name = get_mix_sample_barcode(output_artifact)
                fraction1 = output_artifact.samples[0].udf['Dx Fractienummer']
                fraction2 = output_artifact.samples[1].udf['Dx Fractienummer']
            else:
                fraction = output_artifact.samples[0].udf['Dx Fractienummer']
            if 'Dx Sample 1 norm' in output_artifact.udf:
                input_nunc_1 = output_artifact.udf['Dx Sample 1 norm']
            if 'Dx Sample 2 norm' in output_artifact.udf:
                input_nunc_2 = output_artifact.udf['Dx Sample 2 norm']
            if 'Dx Sample (output)' in output_artifact.udf:
                output_nunc = output_artifact.udf['Dx Sample (output)']
            if sample_mix:
                if input_nunc_1 == fraction1 and input_nunc_2 == fraction2 and output_nunc == mix_name:
                    output_artifact.udf['Dx pipetteer check'] = True
                elif input_nunc_1 == fraction2 and input_nunc_2 == fraction1 and output_nunc == mix_name:
                    output_artifact.udf['Dx pipetteer check'] = True
                else:
                    output_artifact.udf['Dx pipetteer check'] = False
            else:
                if input_nunc_1 == fraction and input_nunc_2 == '' and output_nunc == fraction:
                    output_artifact.udf['Dx pipetteer check'] = True
                else:
                    output_artifact.udf['Dx pipetteer check'] = False
            output_artifact.put()
