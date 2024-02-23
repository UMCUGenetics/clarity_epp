from clarity_epp.export import illumina


def test_get_override_cycles():
    # Magnis prep with legacy index settings (8, 8) - NovaSeq 6000
    assert illumina.get_override_cycles([151, 151], [5, 5], [8, 8], [8, 8], 'RC') == 'U5Y145N1;I8;I8;U5Y145N1'
    # Magnis prep with legacy index settings (8, 8) - NovaSeq X Plus
    assert illumina.get_override_cycles([151, 151], [5, 5], [8, 8], [8, 8], 'F') == 'U5Y145N1;I8;I8;U5Y145N1'

    # Magnis prep with new default index settings (19, 10) - NovaSeq 6000
    assert illumina.get_override_cycles([151, 151], [5, 5], [8, 8], [19, 10], 'RC') == 'U5Y145N1;I8N11;I8N2;U5Y145N1'
    # Magnis prep with new default index settings (19, 10) - NovaSeq X Plus
    assert illumina.get_override_cycles([151, 151], [5, 5], [8, 8], [19, 10], 'F') == 'U5Y145N1;I8N11;N2I8;U5Y145N1'


def test_get_project():
    assert illumina.get_project({'SSv7_1': 1, 'SSv7_2': 0, 'SSv7_3': 0}) == 'SSv7_2'
    assert illumina.get_project({'SSv7_1': 1, 'SSv7_2': 0, 'SSv7_3': 0}, urgent=True) == 'SSv7_1'
    assert illumina.get_project({'SSv7_1': 3, 'SSv7_2': 1, 'SSv7_3': 0}) == 'SSv7_3'
    assert illumina.get_project({'SSv7_1': 3, 'SSv7_2': 1, 'SSv7_3': 0}, urgent=True) == 'SSv7_1'
    assert illumina.get_project({'SSv7_1': 3, 'SSv7_2': 1, 'SSv7_3': 1}) == 'SSv7_2'
    assert illumina.get_project({'SSv7_1': 3, 'SSv7_2': 1, 'SSv7_3': 0}, urgent=True) == 'SSv7_1'
    assert illumina.get_project({'SSv7_1': 9, 'SSv7_2': 5, 'SSv7_3': 5}, urgent=True) == 'SSv7_2'
