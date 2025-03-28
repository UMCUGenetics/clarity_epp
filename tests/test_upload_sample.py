import genologics
import pytest

from clarity_epp.upload import samples


class ResearcherMock:
    def __init__(self, fax, email):
        self.fax = fax
        self.email = email


class ProjectMock:
    def __init__(self, name, researcher):
        self.name = name
        self.researcher = researcher


class ContainertypeMock:
    def __init__(self, name):
        self.name = name


def test_from_helix_file_error(mocker):
    mocker.patch('genologics.lims.Lims.check_version', return_value=None)

    researchers_mock = [ResearcherMock('HelixError', 'test@test.nl')]
    mocker.patch('genologics.lims.Lims.get_researchers', return_value=researchers_mock)

    mocker.patch('genologics.lims.Lims.get_projects', return_value=[])

    project_mock = ProjectMock('TEST', researchers_mock[0])
    mocker.patch('genologics.entities.Project.create', return_value=project_mock)

    container_type_mock = ContainertypeMock('Tube')
    mocker.patch('genologics.entities.Containertype.__new__', return_value=[container_type_mock])

    mocker.patch('clarity_epp.upload.samples.send_email', return_value=None)
    email_settings = {
        'server': 'smtp.test.nl',
        'from': 'from@test.nl',
        'to_import_helix': []

    }

    with pytest.raises(SystemExit) as exception_info:
        with open('tests/data/WL24_01_HelixError.csv', 'r') as helix_file:
            samples.from_helix(genologics.lims.Lims, email_settings, helix_file)

    assert exception_info.type == SystemExit
    assert exception_info.value.code == (
        "Could not correctly parse data from helix export file (werklijst).\n"
        "Row = 1 \t Column = Fractienummer \t UDF = Dx Fractienummer.\n"
        "Please check/update the file and try again. Make sure to remove the project from LIMS before retrying."
    )