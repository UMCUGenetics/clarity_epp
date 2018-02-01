"""Clarity epp configuration."""

# Genologics
baseuri = 'https://change_this_lims.uri'
username = 'change_this'
password = 'change_this'

# Email settings
email = {
    'from': 'from@mail.nl',
    'to': [
        'to_1@mail.nl',
        'to_2@mail.nl'
    ]
}

# Export meetw protocol steps
meetw_zui_processes = ['add', 'protocol', 'steps']
meetw_libprep_processes = ['add', 'protocol', 'steps']
meetw_enrich_processes = ['add', 'protocol', 'steps']
meetw_seq_processes = ['add', 'protocol', 'steps']
