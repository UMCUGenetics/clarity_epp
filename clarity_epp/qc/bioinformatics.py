from genologics.entities import Process

from clarity_epp.qc.utils import transform_sex_multiqc
import config
import sys


def bioinf_qc_check(lims, process_id):
    """Read imported multiqc file and perform quality check

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
    """
    process = Process(lims, id=process_id)

    udf_column = {
        'Dx Gem. dekking': {'column': 'Average Coverage'},
        'Dx CCU': {'column': 'CNV Coverage Uniformity'},
        'Dx Contaminatie': {'column': 'Contamination'},
        'Dx Gevonden geslacht': {'column': 'Sex'},
    }

    # Parse file
    for output in process.all_outputs(unique=True):
        if output.name == 'Dx Data QC':
            try:
                multiqc_file = output.files[0]
                multiqc_file_content = lims.get_file_contents(multiqc_file.id).data.decode('utf-8').split('\n')
                sample_qcs = {}
                for line_index, line in enumerate(multiqc_file_content):
                    if line.startswith('Sample'):
                        header = line.rstrip().split('\t')
                        sample_index = header.index('Sample')
                        for udf in udf_column:
                            udf_column[udf]['index'] = header.index(udf_column[udf]['column'])
                    else:
                        # Parse samples
                        data = line.strip().split('\t')
                        udf_data = {}
                        for udf in udf_column:
                            # Transform specific udf
                            try:
                                if udf in ['Dx Gem. dekking', 'Dx CCU', 'Dx Contaminatie']:
                                    udf_data[udf] = float(data[udf_column[udf]['index']])
                                elif udf == 'Dx Gevonden geslacht':
                                    udf_data[udf] = transform_sex_multiqc(data[udf_column[udf]['index']])
                                else:
                                    udf_data[udf] = data[udf_column[udf]['index']]
                            except (IndexError, ValueError):
                                # Catch parsing errors
                                message = (
                                    'Could not correctly parse data from multiqc file.\n'
                                    f'Row = {line_index+1} \t Column = {udf_column[udf]["column"]} \t UDF = {udf}.\n'
                                    'Please check the file.'
                                )
                                sys.exit(message)
                        sample_name = data[sample_index]
                        sample_qcs[sample_name] = udf_data
            except (IndexError):
                # Catch no file error
                message = ('It seems there is no multiqc file uploaded. Upload the multiqc file and try again.')
                sys.exit(message)

    # Fill sample udfs and safe family info
    family_info = {}
    for input in process.all_inputs():
        if input.type == 'Analyte':
            flowcell = input.udf['Dx Sequencing Run ID'].split('_')[-1]
            sample_flowcell = f'{input.name}_{flowcell}'
            for udf in udf_column:
                if sample_flowcell in sample_qcs:
                    input.udf[udf] = sample_qcs[sample_flowcell][udf]
            input.put()
            family_info[input.name] = {}
            family_info[input.name]['number'] = input.samples[0].udf['Dx Familienummer']
            family_info[input.name]['status'] = input.samples[0].udf['Dx Familie status']
            if 'Dx CCU' in input.udf:
                family_info[input.name]['ccu'] = input.udf['Dx CCU']

    # Perform QC per input
    for input in process.all_inputs():
        if input.type == 'Analyte':
            udfs = ['Dx Gem. dekking', 'Dx CCU', 'Dx Contaminatie', 'Dx Gevonden geslacht']
            qc_udf_not_filled = any(udf not in input.udf for udf in udfs)
            if not qc_udf_not_filled:
                qc_conclusion = ''
                message = ''
                # QC coverage check
                if input.udf['Dx Gem. dekking'] < config.bioinformatics_qc_requirements_srWGS['Coverage']:
                    qc_conclusion += 'Dekking afgekeurd. '
                    message += 'De gemiddelde dekking {qc} is onder {req}x. '.format(
                        qc=input.udf['Dx Gem. dekking'],
                        req=config.bioinformatics_qc_requirements_srWGS['Coverage'],
                    )
                # QC CCU check
                if input.udf['Dx CCU'] > config.bioinformatics_qc_requirements_srWGS['CCU']:
                    family_status = family_info[input.name]["status"]
                    # Parent
                    if family_status == 'Ouder':
                        family_number = family_info[input.name]['number']
                        for fraction in family_info:
                            if family_info[fraction]['number'] == family_number and family_info[fraction]['status'] == 'Kind':
                                child = fraction
                        if child:
                            child_ccu = family_info[child]["ccu"]
                            # CCU child too high
                            if child_ccu > config.bioinformatics_qc_requirements_srWGS['CCU_index']:
                                qc_conclusion += 'CCU afgekeurd. '
                                message += \
                                    'De CCU waarde {qc} is boven {req}. ' \
                                    'En de CCU waarde van kind ({child}) {qc_index} is boven {req_index}. '.format(
                                        qc=input.udf['Dx CCU'],
                                        req=config.bioinformatics_qc_requirements_srWGS['CCU'],
                                        child=child,
                                        qc_index=child_ccu,
                                        req_index=config.bioinformatics_qc_requirements_srWGS['CCU_index'],
                                    )
                            # CCU child low enough
                            elif child_ccu <= config.bioinformatics_qc_requirements_srWGS['CCU_index']:
                                qc_conclusion += 'CCU goedgekeurd. '
                                message += \
                                    'De CCU waarde {qc} is boven {req}. ' \
                                    'Maar de CCU waarde van kind ({child}) {qc_index} is onder {req_index}. '.format(
                                        qc=input.udf['Dx CCU'],
                                        req=config.bioinformatics_qc_requirements_srWGS['CCU'],
                                        child=child,
                                        qc_index=child_ccu,
                                        req_index=config.bioinformatics_qc_requirements_srWGS['CCU_index'],
                                    )
                        # No child in step
                        else:
                            print(f'No child for family {family_number} in this step')
                            qc_conclusion += 'CCU onbekend. '
                            message += \
                                'De CCU waarde {qc} is boven {req}. ' \
                                'Het betreft een ouder, maar kind van is niet aanwezig in deze stap. '.format(
                                    qc=input.udf['Dx CCU'],
                                    req=config.bioinformatics_qc_requirements_srWGS['CCU'],
                                )
                    # Child
                    else:
                        qc_conclusion += 'CCU afgekeurd. '
                        message += 'De CCU waarde {qc} is boven {req}. Het betreft een kind. '.format(
                            qc=input.udf['Dx CCU'],
                            req=config.bioinformatics_qc_requirements_srWGS['CCU'],
                        )
                # QC contamination check
                if input.udf['Dx Contaminatie'] > config.bioinformatics_qc_requirements_srWGS['Contamination']:
                    qc_conclusion += 'Contaminatie afgekeurd. '
                    message += 'De contaminatie waarde {qc} is boven {req}. '.format(
                        qc=input.udf['Dx Contaminatie'],
                        req=config.bioinformatics_qc_requirements_srWGS['Contamination'],
                    )
                # QC sex check
                if input.udf['Dx Gevonden geslacht'] != input.samples[0].udf['Dx Geslacht']:
                    qc_conclusion += 'Geslacht afgekeurd. '
                    message += 'Het gevonden geslacht {qc} komt niet overeen met het bekende geslacht {req}. '.format(
                        qc=input.udf['Dx Gevonden geslacht'],
                        req=input.samples[0].udf['Dx Geslacht'],
                    )

                # If any qc does not meet qc requirement fill 'Afwijkingen' udfs
                if qc_conclusion:
                    input.udf['Dx afwijkingen oorzaak'] = 'Data'
                    if 'afgekeurd' in qc_conclusion:
                        input.udf['Dx afwijkingen uitleg'] = f'Conclusie: afgekeurd (Uitleg: {message.strip()})'
                    elif 'onbekend' in qc_conclusion:
                        input.udf['Dx afwijkingen uitleg'] = f'Conclusie: onbekend (Uitleg: {message.strip()})'
                    elif 'goedgekeurd' in qc_conclusion:
                        input.udf['Dx afwijkingen uitleg'] = f'Conclusie: goedgekeurd (Uitleg: {message.strip()})'

                # QC check complete
                input.udf['Dx QC check'] = True
                input.put()
