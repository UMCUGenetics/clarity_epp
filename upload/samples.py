"""Sample upload epp functions."""
from genologics.entities import Sample, Project, Containertype, Container

hand = False


def letter_to_bool(letter):
    """Transform letter (Y/N) to Bool."""
    if letter.upper() == 'J':
        return True
    elif letter.upper() == 'N':
        return False


def value_to_bool(value):
    """Transform value to Bool."""
    if len(value) != 0:
        return True
    elif len(value) == 0:
        return False


def from_helix(lims, input_file):
    """Upload samples from helix export file."""
    project = Project(lims, id='ERN151')
    container_type = Containertype(lims, id='2')  # Tube

    input_file.readline()  # expect header on first line, skip it.
    for line in input_file:
        data = line.rstrip().split('","')
        sample_name = data[1]

        if value_to_bool(data[5]) == False and letter_to_bool(data[6]) == False and letter_to_bool(data[8]) == False and letter_to_bool(data[9]) == False and data[4] == 'BL':
            hand = False
        else:
            hand = True

        if lims.get_sample_number(name=sample_name):
            print "ERROR: Sample {sample_name} already exists.".format(sample_name=sample_name)
        else:
            udf_data = {
                'Sample Type': 'DNA isolated',  # required lims input
                'Dx Onderzoeknummer': data[0].replace('"',''),
                'Dx Fractienummer': data[2],
                'Dx Concentratie (ng/uL)': data[3],
                'Dx Materiaal type': data[4],
                'Dx Foetus': value_to_bool(data[5]),
                'Dx Overleden': letter_to_bool(data[6]),
                'Dx Opslaglocatie': data[7],
                'Dx Spoed': letter_to_bool(data[8]),
                'Dx NICU Spoed': letter_to_bool(data[9]),
                'Dx Persoons ID': data[10],
                'Dx Werklijstnummer': data[11],
                'Dx Unummer': data[12],
                'Dx Geslacht': data[13],
                'Dx Geboortejaar': data[14],
                'Dx meet ID': data[15],
                'Dx Stoftest code': data[16],
                'Dx Stoftest omschrijving': data[17],
                'Dx Helix indicatie': data[18].replace('"',''),
                'Dx Handmatig': hand,
            }
            container = Container.create(lims, type=container_type)
            Sample.create(lims, container=container, position='1:1', project=project, name=sample_name, udf=udf_data)
