"""Sample upload epp functions."""
from genologics.entities import Sample, Project, Containertype, Container


def letter_to_bool(letter):
    """Transform letter (Y/N) to Bool."""
    if letter.upper() == 'J':
        return True
    elif letter.upper() == 'N':
        return False


def from_helix(lims, input_file):
    """Upload samples from helix export file."""
    project = Project(lims, id='ERN151')
    container_type = Containertype(lims, id='2')  # Tube

    input_file.readline()  # expect header on first line, skip it.
    for line in input_file:
        data = line.rstrip().split(';')
        sample_name = data[0]

        if lims.get_sample_number(name=sample_name):
            print "ERROR: Sample {sample_name} already exists.".format(sample_name=sample_name)
        else:
            udf_data = {
                'Sample Type': 'DNA isolated',  # required lims input
                'Dx Fractienummer': data[1],
                'Dx Concentratie (ng/uL)': data[2],
                'Dx Materiaal type': data[3],
                #'Dx Foetus': data[4],  # is a date?
                'Dx Overleden': letter_to_bool(data[5]),
                'Dx Opslaglocatie': data[6],
                'Dx Spoed': letter_to_bool(data[7]),
                'Dx NICU Spoed': letter_to_bool(data[8]),
                'Dx Persoons ID': data[9],
                'Dx Werklijstnummer': data[10],
                'Dx Unummer': data[11],
                'Dx Geslacht': data[12],
                'Dx Geboortejaar': data[13],
                'Dx meet ID': data[14],
                'Dx Stoftest code': data[15],
                'Dx Stoftest omschrijving': data[16],
                'Dx Helix indicatie': data[17],
            }
            container = Container.create(lims, type=container_type)
            Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
