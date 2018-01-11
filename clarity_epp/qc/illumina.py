"""Illumina qc functions."""
from genologics.entities import Process


def set_avg_q30(lims, process_id):
    """Calculate average % Bases >=Q30."""
    process = Process(lims, id=process_id)
    artifact = process.analytes()[0][0]

    artifact.udf['Dx Average % Bases >=Q30'] = (artifact.udf['% Bases >=Q30 R1'] + artifact.udf['% Bases >=Q30 R2']) / 2.0
    artifact.put()
