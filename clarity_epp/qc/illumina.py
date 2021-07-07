"""Illumina qc functions."""
from genologics.entities import Process


def set_avg_q30(lims, process_id):
    """Calculate average % Bases >=Q30."""
    process = Process(lims, id=process_id)
    artifact = process.analytes()[0][0]

    if all([udf in artifact.udf for udf in ['% Bases >=Q30 R1', 'Yield PF (Gb) R1', '% Bases >=Q30 R2', 'Yield PF (Gb) R2']]):
        r1_q30 = artifact.udf['% Bases >=Q30 R1']
        r1_yield = artifact.udf['Yield PF (Gb) R1']
        r2_q30 = artifact.udf['% Bases >=Q30 R2']
        r2_yield = artifact.udf['Yield PF (Gb) R2']

        average_q30 = (r1_q30*r1_yield + r2_q30*r2_yield) / (r1_yield+r2_yield)

        artifact.udf['Dx Average % Bases >=Q30'] = average_q30
        artifact.put()
