"""Pipetting  placement functions."""

from genologics.entities import Process

def check_nunc_input_nunc_output(lims, process_id):
    """Check nuncs."""
    process = Process(lims, id=process_id)
    for output_artifact in process.all_outputs():
        if output_artifact.type == 'Analyte':
            input_nunc_1 = ''
            input_nunc_2 = ''
            output_nunc = ''
            input_combined = ''
            if 'Dx Sample 1 norm' in output_artifact.udf:
                input_nunc_1 = output_artifact.udf['Dx Sample 1 norm']
            if 'Dx Sample 2 norm' in output_artifact.udf:
                input_nunc_2 = output_artifact.udf['Dx Sample 2 norm']
            if 'Dx Sample (output)' in output_artifact.udf:
                output_nunc = output_artifact.udf['Dx Sample (output)']
            if input_nunc_1 and input_nunc_2:
                input_combined = '{input_nunc_1}-{input_nunc_2}'.format(input_nunc_1=input_nunc_1, input_nunc_2=input_nunc_2)
            elif input_nunc_1:
                input_combined = input_nunc_1
            if input_combined and output_nunc:
                if input_combined == output_nunc:
                    output_artifact.udf['Dx pipetteer check'] = True
                    output_artifact.put()
