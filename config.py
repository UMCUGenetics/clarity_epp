"""Clarity epp configuration."""

# Genologics
baseuri = 'https://change_this_lims.uri'
username = 'change_this'
password = 'change_this'

# Email settings
email = {
    'server': 'smtp.server.nl',
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
    'NGS_027': '1106',  # DEV Dx smMIP Fingerprint v1.2
    'NGS_025': '1201',  # DEV Dx Exoom Magnis v1.0
}

stoftestcode_mip = 'NGS_027'
stoftestcode_wes = 'NGS_025'

# Export meetw protocol steps WES
meetw_zui_wes_processes = [
    'Dx Sample registratie zuivering v1.1',
    'Dx Hamilton uitvullen v1.1',
    'Dx Hamilton zuiveren v1.1',
    'Dx Zuiveren gDNA manueel v1.1',
    'Dx manueel gezuiverd placement v1.2',
    'Dx gDNA Normalisatie Caliper v1.1',
    'Dx Fragmenteren v1.0'
]

meetw_sampleprep_wes_processes = ['Dx Library Prep & Target Enrichment Magnis v1.0']

meetw_seq_wes_processes = [
    'Dx Multiplexen Enrichment pools Magnis v1.0',
    'Dx Multiplexen sequence pool v1.2',
    'Dx Library pool denatureren en laden (NovaSeq) v1.3',
    'AUTOMATED - NovaSeq Run (NovaSeq 6000 v3.1)',
    'Dx QC controle Lab sequencen v1.1'
]

# Export meetw protocol steps MIP
meetw_libprep_mip_processes = [
    'Dx Sample registratie v1.0',
    'Dx Hamilton uitvullen v1.1',
    'Dx gDNA Normalisatie Caliper v1.1',
    'Dx gDNA handmatige normalisatie v1.0',
    'Dx Capture v1.0',
    'Dx Exonuclease behandeling v1.0',
    'Dx PCR na exonuclease behandeling v1.0',
    'Dx smMIP multiplexen & BBSS sequence pool v1.0'
]

meetw_seq_mip_processes = [
    'Dx smMIP sequence pool verdunning v1.0',
    'Dx Library pool denatureren en laden (Nextseq) v1.1',
    'Dx NextSeq Run v1.1',
    'Dx QC controle Lab sequencen v1.1',
]

# Sequencer types
sequence_process_types = [
    'Dx NextSeq Run v1.0', 'Dx NextSeq Run v1.1',
    'Dx Automated NovaSeq Run (standaard) v1.0', 'Dx Automated NovaSeq Run (standaard) v1.1',
    'AUTOMATED - NovaSeq Run (NovaSeq 6000 v3.1)',
]

# Post sequencing workflow
sequencing_workflow = '1301'  # DEV Dx Illumina Sequencing v1.0
post_sequencing_workflow = '902'  # DEV Dx Bioinformatica analyses v1.0
post_bioinf_workflow = {  # Contains workflow and workflow stage (number) for single or trio samples
    'NGS_025': {'single': ['1401', 0], 'trio': ['1401', 1]},  # WES : DEV Dx NGS WES onderzoeken afronden v1.1
    'NGS_027': {'single': ['1202', 0], 'trio': ['1202', 0]}  # MIP : DEV Dx NGS smMIP onderzoeken afronden v1.0
}

research_stoftest_code = 'NGS_023'

# Research Onderzoeksindicatie
research_onderzoeksindicatie_project = {
    'PD-GRID': 'knoers_grid'
}
