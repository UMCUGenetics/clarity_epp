from clarity_epp.upload import utils


def test_txt_to_bool():
    assert utils.txt_to_bool('J')
    assert not utils.txt_to_bool('N')
    assert utils.txt_to_bool('TRUE')
    assert not utils.txt_to_bool('FALSE')


def test_transform_sex():
    assert utils.transform_sex('M') == 'Man'
    assert utils.transform_sex('V') == 'Vrouw'
    assert utils.transform_sex('O') == 'Onbekend'


def test_transform_sample_name():
    assert utils.transform_sample_name('D01/2016') == 'D012016'
