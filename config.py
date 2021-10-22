"""Clarity epp configuration."""

# Genologics
baseuri = 'https://change_this_lims.uri'
username = 'change_this'
password = 'change_this'

# Email settings
email = {
    'from': 'from@email.nl',
    'to_import_helix': [
        'to_1@mail.nl',
    ],
    'to_sequencing_run_complete': [
        'to_1@mail.nl',
    ]
}

# Import samples: stoftestcode to workflow
stoftestcode_workflow = {
    'NGS_008': '1107',  # DEV Dx Exoom KAPA v1.9
    'NGS_022': '1107',  # DEV Dx Exoom KAPA v1.9
    'NGS_023': '1107',  # DEV Dx Exoom KAPA v1.9
    'NGS_xxx': '1106',  # DEV Dx smMIP Fingerprint v1.2
    'NGS_025': '1253',  # DEV Dx Exoom Magnis test v1.1
}

# Export meetw protocol steps
meetw_zui_processes = ['Dx Sample registratie zuivering v1.0', 'Dx Hamilton uitvullen v1.0', 'Dx Hamilton zuiveren v1.0', 'Dx Zuiveren gDNA manueel v1.0', 'Dx manueel gezuiverd placement v1.0', 'Dx gDNA Normalisatie Caliper v1.0', 'Dx Fragmenteren & BBSS v1.0']
meetw_libprep_processes = ['Dx LibraryPrep Caliper KAPA v1.0', 'Dx Library Prep amplificatie & clean up KAPA v1.0']
meetw_enrich_processes = ['Dx Multiplexen library prep v2.0', 'Dx Enrichment DNA fragments v1.0', 'Dx Post Enrichment clean up v1.0', 'Dx Aliquot Post Enrichment (clean) v1.0', 'Dx Post Enrichment PCR & clean up v1.0', 'Dx Aliquot Post Enrichment PCR (clean) v1.0']
meetw_seq_processes = ['Dx Multiplexen library pool v1.1', 'Dx Multiplexen sequence pool v1.1', 'Dx Library pool denatureren en laden (NextSeq) v1.0', 'Dx NextSeq Run v1.0', 'Dx Library pool denatureren en laden (NovaSeq) v1.0', 'Dx Automated NovaSeq Run (standaard) v1.0', 'Dx QC controle Lab sequencen v1.0']

# Sequencer types
sequence_process_types = ['Dx NextSeq Run v1.0', 'Dx Automated NovaSeq Run (standaard) v1.0']

# Post sequencing workflow
sequencing_workflow = '1301' # DEV Dx Illumina Sequencing v1.0
post_sequencing_workflow = '901'  # DEV Dx Bioinformatica analyses v1.0
post_bioinf_workflow = '902' # DEV Dx NGS onderzoeken afronden v1.0
research_stoftest_code = 'NGS_023'

# Research Onderzoeksindicatie
research_onderzoeksindicatie_project = {
    'PD-GRID': 'knoers_grid'
}