import sys

from genologics.entities import Process, Step
from clarity_epp.export.email import send_mail_manager_review
from clarity_epp.qc.utils import transform_sex_multiqc

import config


def bioinf_qc_check(lims, process_id):
    """Read imported multiqc file and perform quality check

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
    """
    process = Process(lims, id=process_id)

    udf_columns = {
        'Dx Gem. dekking': {'column': 'Average Coverage', 'transform': float},
        'Dx CCU': {'column': 'CNV Coverage Uniformity', 'transform': float},
        'Dx Contaminatie': {'column': 'Contamination', 'transform': float},
        'Dx Gevonden geslacht': {'column': 'Sex', 'transform': transform_sex_multiqc},
    }
    sample_qcs = parse_file(process, lims, udf_columns)
    family_information = get_family_info(process, sample_qcs, udf_columns)
    qc_check(process, udf_columns, family_information)


def parse_file(process, lims, udf_columns):
    """Import multiqc file 

    Args:
        process: Lims process
        lims (object): Lims connection
        udf_columns (dict): Dictonary with udf columns to parse

    Returns:
        dict: Dictonary with sample qcs
    """
    sample_qcs = {}
    for output in process.all_outputs(unique=True):
        if output.name == 'Dx Data QC':
            try:
                multiqc_file = output.files[0]
                # Get multiqc file content, strip empty lines at end of file and split on newlines
                multiqc_file_content = lims.get_file_contents(multiqc_file.id).data.decode('utf-8').rstrip().split('\n')
                for line_index, line in enumerate(multiqc_file_content):
                    data = line.rstrip().split('\t')
                    if len(data) < 5: # if no value for sex assigned add None
                        data.append(None)
                    if line.startswith('Sample'):
                        sample_index = data.index('Sample')
                        for udf in udf_columns:
                            udf_columns[udf]['index'] = data.index(udf_columns[udf]['column'])
                    else:
                        # Parse samples
                        udf_data = {}
                        for udf in udf_columns:
                            try:
                                if data[udf_columns[udf]['index']] in ['NA', None, '']:
                                    data[udf_columns[udf]['index']] = None
                                    udf_data[udf] = data[udf_columns[udf]['index']]
                                if udf == 'Dx CCU' and data[udf_columns[udf]['index']] is None:
                                    data[udf_columns[udf]['index']] = -1
                                    udf_data[udf] = data[udf_columns[udf]['index']]
                                if data[udf_columns[udf]['index']]: 
                                    if 'transform' in udf_columns[udf]:
                                        udf_data[udf] = udf_columns[udf]['transform'](data[udf_columns[udf]['index']])
                                    else:
                                        udf_data[udf] = data[udf_columns[udf]['index']]
                            except (IndexError, ValueError):
                                # Catch parsing errors
                                message = (
                                    'Could not correctly parse data from multiqc file.\n'
                                    f'Row = {line_index+1} \t Column = {udf_columns[udf]["column"]} \t UDF = {udf}.\n'
                                    'Please check the file.'
                                )
                                sys.exit(message)
                        sample_name = data[sample_index]
                        sample_qcs[sample_name] = udf_data
            except (IndexError):
                # Catch no file error
                message = ('It seems there is no multiqc file uploaded. Upload the multiqc file and try again.')
                sys.exit(message)
    return sample_qcs
    

def get_family_info(process, sample_qcs, udf_columns):
    """Retrieve family information

    Args:
        process (object): Lims process/step
        sample_qcs (dict): Dictonary with sample qcs
        udf_columns (dict): Dictonary with udf columns

    Returns:
        dict: Dictonary with family information
    """   
    family_info = {}
    for input in process.analytes()[0]:
        flowcell = input.udf['Dx Sequencing Run ID'].split('_')[-1]
        sample_flowcell = f'{input.name}_{flowcell}'
        for udf in udf_columns:
            if sample_flowcell in sample_qcs:
                if sample_qcs[sample_flowcell][udf] is not None:   
                    input.udf[udf] = sample_qcs[sample_flowcell][udf]
        input.put()
        family_info[input.name] = {}
        family_info[input.name]['number'] = input.samples[0].udf['Dx Familienummer']
        family_info[input.name]['status'] = input.samples[0].udf['Dx Familie status']
        if 'Dx CCU' in input.udf:
            family_info[input.name]['ccu'] = input.udf['Dx CCU']
    return family_info


def qc_check(process, udf_columns, family_info):
    """Perform QC check on samples in process

    Args:
        process (object): Lims process/step 
        udf_columns (dict): Dictonary with udf columns
        family_info (dict): Dictonary with family information
    """
    for input in process.analytes()[0]:
        udfs = list(udf_columns.keys())
        if any(udf not in input.udf for udf in udfs):
            continue
        qc_requirements = config.bioinformatics_qc_requirements_srWGS
        qc_message = []
        qc_conclusion = ''
        if input.udf['Dx Gem. dekking'] < qc_requirements['Coverage'] or input.udf['Dx Gem. dekking'] is None:
            qc_message, qc_conclusion = qc_coverage_fail(input, qc_conclusion, qc_message, qc_requirements)
        qc_message, qc_conclusion = qc_ccu_check(input, qc_conclusion, qc_message, family_info, qc_requirements)
        if input.udf['Dx Contaminatie'] > qc_requirements['Contamination'] or input.udf['Dx Contaminatie'] is None: 
            qc_message, qc_conclusion = qc_contamination_fail(input, qc_conclusion, qc_message, qc_requirements) 
        if input.samples[0].udf.get("Dx Foetus") is True and input.samples[0].udf.get('Dx Geslacht') == 'Onbekend':
            qc_message, qc_conclusion = no_check_foetus(qc_message, qc_conclusion)
        else:
            if input.udf['Dx Gevonden geslacht'] != input.samples[0].udf['Dx Geslacht'] or input.udf['Dx Gevonden geslacht'] is None:
                qc_message, qc_conclusion = qc_sex_fail(input, qc_conclusion, qc_message)
        if qc_conclusion:
            input = qc_mark_failed(input, qc_conclusion, qc_message)
        if 'Dx afwijkingen oorzaak' not in input.udf:
            input.udf['Dx QC check'] = True
        elif (input.udf['Dx afwijkingen oorzaak'] and
                input.udf['Dx afwijkingen uitleg'].startswith('Conclusie: goedgekeurd')):
            input.udf['Dx QC check'] = True
        input.put()


def qc_coverage_fail(input, qc_conclusion, qc_message, qc_requirements):
    """Add conclusion and message for low coverage QC

    Args:
        input (Artifact): Lims artifact
        qc_conclusion (str): QC conclusion
        qc_message (list): QC message 
        qc_requirements (dict): Dictonary with qc requirements

    Returns:
        list: qc_message for low coverage
        str: Updated QC conclusion 
    """
    qc_conclusion += 'Dekking afgekeurd.'
    qc_message.append(
        f"De gemiddelde dekking {input.udf['Dx Gem. dekking']} is onder "
        f"{qc_requirements['Coverage']}x.")
    return qc_message, qc_conclusion 


def qc_ccu_check(input, qc_conclusion, qc_message, family_info, qc_requirements):
    """Check CCU QC and write conclusion and message if failed

    Args:
        input (Artificat): Lims artifact
        qc_conclusion (str):: QC conclusion
        qc_message (list): QC message 
        family_info (dict): Dictonary with family information

    Returns:
        list: qc_message for high CCU
        str: Updated QC conclusion
    """
    family_status = family_info[input.name]["status"]
    ccu = input.udf['Dx CCU']
    if family_status == 'Ouder':
        threshold = qc_requirements['CCU_parent']
        label = 'ouder'
    elif family_status == 'Kind':
        threshold = qc_requirements['CCU_child']
        label = 'kind'
    else:
        return qc_conclusion, qc_message
    if ccu is None or ccu > threshold:
        qc_conclusion += 'CCU afgekeurd.'
        qc_message.append(
            f"De CCU waarde {ccu} is boven {threshold}. Het betreft een {label}."
        )
    if ccu == -1:
        qc_conclusion += 'CCU afgekeurd.'
        qc_message.append(
            f"De CCU waarde is NA. Het betreft een {label}."
        )

    return qc_message, qc_conclusion

            
def qc_contamination_fail(input, qc_conclusion, qc_message, qc_requirements):
    """Add conclusion and message for high contamination QC

    Args:
        input (Artificat): Lims artifact
        qc_conclusion (str): QC conclusion
        qc_message (list): QC message 

    Returns:
        list: qc_message for high contamination
        str: Updated QC conclusion
    """    
    qc_conclusion += 'Contaminatie afgekeurd.'
    qc_message.append(
        f"De contaminatie waarde {input.udf['Dx Contaminatie']} is boven "
        f"{qc_requirements['Contamination']}.")
    return qc_message, qc_conclusion


def qc_sex_fail(input, qc_conclusion, qc_message):
    """Add conclusion and message for gender fail 

    Args:
        input (Artificat): Lims artifact
        qc_conclusion (str): QC conclusion
        qc_message (list): QC message 
    Returns:
        list: qc_message for gender fail
        str: Updated QC conclusion
    """    
    qc_conclusion += 'Geslacht afgekeurd.'
    qc_message.append(
        f"Het gevonden geslacht {input.udf['Dx Gevonden geslacht']} komt niet overeen met het bekende geslacht "
        f"{input.samples[0].udf['Dx Geslacht']}.")
    return qc_message, qc_conclusion


def no_check_foetus(qc_message, qc_conclusion):
    """Add conclusion and message when gender check is skipped for feutus samples

    Args:
        qc_conclusion (str): QC conclusion
        qc_message (list): QC message 

    Returns:
        Updated QC conclusion and message when feutus gender check is skipped
    """
    qc_conclusion += 'Geslacht goedgekeurd.'
    qc_message.append(
        "Prenataal sample (Dx Foetus = True) met onbekend geslacht,"
        " geslachtscontrole is niet uitgevoerd."
    )
    return qc_message, qc_conclusion


def qc_mark_failed(input, qc_conclusion, qc_message):      
    """Fill in 'Afwijkingen' udfs for failed qc
    
    Args:
        input (Artificat): Lims artifact
        qc_conclusion (str): QC conclusion
        qc_message (list): QC message 
        
    Returns:
        Artifact: with updated 'Afwijkingen' udfs
    """      
    explanation = ' '.join(qc_message)
    input.udf['Dx afwijkingen oorzaak'] = 'Data'
    if 'afgekeurd' in qc_conclusion:
        input.udf['Dx afwijkingen uitleg'] = f'Conclusie: afgekeurd (Uitleg: {explanation})'
    elif 'onbekend' in qc_conclusion:
        input.udf['Dx afwijkingen uitleg'] = f'Conclusie: onbekend (Uitleg: {explanation})'
    elif 'goedgekeurd' in qc_conclusion:
        input.udf['Dx afwijkingen uitleg'] = f'Conclusie: goedgekeurd (Uitleg: {explanation})'
    return input

def fill_next_step_and_send_mail(lims, process_id):
    """
    Fill in values for Next step either request manager review or mark protocol as complete.
    Send email to manager if review is requested.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID

    """
    step = Step(lims,  id=process_id)
    review_trigger = "conclusie: afgekeurd"
    actions = step.actions
    new_next_actions = []
    for action in actions.next_actions:
        artifact = action["artifact"]
        artifact.get()
        text = (artifact.udf.get("Dx afwijkingen uitleg", "") or "").lower().strip()
        needs_review = review_trigger.lower() in text

        if needs_review:
            new_next_actions.append({
                "artifact": artifact,
                "action": "review",
            })
        else:
            new_next_actions.append({
                "artifact": artifact,
                "action": "complete",
            })

    actions.next_actions = new_next_actions
    actions.put()
    if any(action.get("action") == "review" for action in new_next_actions):
        step_url = get_step_url(process_id)
        send_mail_manager_review(config.email, step_url)
    return


def get_step_url(process_id):
    """
    Get clarity 'work-complete' URL for step.

    Args:
        process_id (str): Process ID

    Returns:
        str: url
    """
    step_id = process_id.split("-")[1]
    #To do adjust to not test server
    return f"https://usf-lims-test.op.umcutrecht.nl/clarity/work-complete/{step_id}"

