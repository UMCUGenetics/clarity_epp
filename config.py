"""Clarity epp configuration."""

# Genologics
baseuri = 'https://change_this_lims.uri'
username = 'change_this'
password = 'change_this'
api_timeout = 60

# Email settings
email = {
    'server': 'smtp.server.nl',
    'from': 'from@email.nl',
    'to_import_helix': [
        'to_1@mail.nl',
    ],
    'to_import_glims': [
        'to_1@mail.nl',
    ],
    'to_sequencing_run_complete': [
        'to_1@mail.nl',
    ]
}

# Import samples: stoftestcode to workflow
stoftestcode_wes = 'NGS_025'
stoftestcode_wes_duplo = 'NGS_028'
stoftestcode_mip = 'NGS_027'
stoftestcode_research = 'NGS_023'

stoftestcode_workflow = {
    stoftestcode_wes: '1852',  # DEV Dx Exoom Magnis v2.1
    stoftestcode_wes_duplo: '1852',  # DEV Dx Exoom Magnis v2.1
    stoftestcode_mip: '1651',  # DEV Dx smMIP v1.2
}

# Import samples: fixed workflows
pg_workflow = '1901'  # Dx Library Prep Mirocanvas test1

# Export meetw protocol steps WES
meetw_zui_wes_processes = [
    'Dx Sample registratie zuivering v1.1',
    'Dx Sample registratie zuivering v1.2',
    'Dx Hamilton uitvullen v1.1',
    'Dx Hamilton zuiveren v1.1',
    'Dx Zuiveren gDNA manueel v1.1',
    'Dx manueel gezuiverd placement v1.2',
    'Dx gDNA Normalisatie Caliper v1.1',
    'Dx Uitvullen en zuiveren (Fluent 480) v1.0',
    'Dx Uitvullen en zuiveren (Fluent 480) v1.1',
    'Dx Normaliseren (Fluent 480) v1.0',
    'Dx gDNA handmatige normalisatie WES v1.0',
    'Dx gDNA handmatige normalisatie WES v1.1',
]

meetw_sampleprep_wes_processes = [
    'Dx Fragmenteren v1.0',
    'Dx Library Prep & Target Enrichment Magnis v1.0',
    'Dx Library Prep & Target Enrichment Magnis v1.1',
]

meetw_seq_wes_processes = [
    'Dx Multiplexen Enrichment pools Magnis v1.0',
    'Dx Multiplexen sequence pool v1.2',
    'Dx Library pool denatureren en laden (NovaSeq) v1.3',
    'AUTOMATED - NovaSeq Run (NovaSeq 6000 v3.1)',
    'Dx QC controle Lab sequencen v1.1',
    'Dx NovaSeq QC controle Lab sequencen v1.3',
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
    'Dx smMIP multiplexen & BBSS sequence pool v1.0',
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
sequencing_workflow = '1701'  # DEV Dx Illumina Sequencing v1.2
post_sequencing_workflow = '1204'  # DEV Dx Bioinformatica analyses v1.1
post_bioinf_workflow = '1803'  # DEV Dx NGS WES onderzoeken afronden v2.0

# Research Onderzoeksindicatie
research_onderzoeksindicatie_project = {
    'PD-GRID': 'knoers_grid'
}
