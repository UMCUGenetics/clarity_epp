"""Clarity epp package."""


def get_sequence_name(sample):
    """Generate sequence name."""
    # Set fam_status
    if sample.udf['Dx Familie status'] == 'Kind':
        fam_status = 'C'
    elif sample.udf['Dx Familie status'] == 'Ouder':
        fam_status = 'P'

    # Set sex
    if sample.udf['Dx Geslacht'] == 'Man':
        sex = 'M'
    elif sample.udf['Dx Geslacht'] == 'Vrouw':
        sex = 'F'
    elif sample.udf['Dx Geslacht'] == 'Onbekend':
        sex = 'U'

    sequence_name = '{unummer}{fam_status}{sex}{monsternumer}'.format(
        unummer=sample.udf['Dx Unummer'],
        fam_status=fam_status,
        sex=sex,
        monsternummer=sample.udf['Dx Monsternummer']
    )

    return sequence_name
