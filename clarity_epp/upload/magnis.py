"""Magnis export upload epp functions."""

from genologics.entities import Process
import xmltodict


def results(lims, process_id):
    """Upload magnis export to process."""
    process = Process(lims, id=process_id)
    lot_error = False

    for output_file in process.result_files():
        if output_file.name == 'Magnis export file':
            magnis_xml_file = output_file.files[0]
            magnis_data = xmltodict.parse(lims.get_file_contents(magnis_xml_file.id))

            # Save lot nunmbers and check sample input strip barcode
            for labware in magnis_data['RunInfo']['LabwareInfos']['Labware']:
                if labware['@Name'] == 'Probe Input Strip':
                    process.udf['lot # SureSelect v7'] = labware['@LotNumber']
                elif labware['@Name'] == 'Reagent Plate':
                    process.udf['lot # Magnis Sureselect XT HS reagent plate'] = labware['@LotNumber']
                elif labware['@Name'] == 'Beads/Buffers Plate':
                    process.udf['lot # Magnis SureSelect XT Beads/Buffers Plate'] = labware['@LotNumber']
                elif labware['@Name'] == 'Index Strip':
                    process.udf['lot # Dual BC strip'] = labware['@LotNumber']
                    index_strip_number = int(labware['@IndexStrip'])
                elif labware['@Name'] == 'Reagent Strip':
                    process.udf['lot # BR Oligo strip (blockers)'] = labware['@LotNumber']
                elif (
                    labware['@Name'] == 'Sample Input Strip' and
                    process.udf['Barcode sample input strip'] != labware['@BarCode']
                ):
                    lot_error = True

    # Check sample reagents and fill Lotnr check flag
    for output in process.analytes()[0]:
        label_index_nunmber = int(output.reagent_labels[0][3:5])
        if lot_error or label_index_nunmber != index_strip_number:
            output.udf['Lotnr check'] = False
        else:
            output.udf['Lotnr check'] = True
        output.put()
    process.put()
