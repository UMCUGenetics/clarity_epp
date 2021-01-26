#  <workflow_name>

# Step 1a - Export workflow
java -jar config-slicer.jar \
    -o custom \
    -s <dev_server> \
    -u <username> \
    -p <password> \
    -m <workflow_name>_workflowManifest.txt \
    -w '<workflow_name>'

# Step 1b - Export workflow
java -jar config-slicer.jar \
    -o export \
    -s <dev_server> \
    -u <username> \
    -p <password> \
    -m <workflow_name>_workflowManifest.txt \
    -k <workflow_name>_workflowManifest.xml

# Step 2 - Compare workflow
java -jar config-slicer.jar \
    -o validate \
    -s <prod_server> \
    -u <username> \
    -p <password> \
    -k <workflow_name>_workflowManifest.xml \
    > validate_before.out

#  Step 3a - Import workflow
java -jar config-slicer.jar \
    -o import \
    -s <prod_server> \
    -u <username> \
    -p <password> \
    -k <workflow_name>_workflowManifest.xml \
    > import.out

#  Step 3b - Import workflow
# Needs promt don't redirect output!
java -jar config-slicer.jar \
    -o importAndOverwrite \
    -s <prod_server> \
    -u <username> \
    -p <password> \
    -k <workflow_name>_workflowManifest.xml

# Step 4 - Compare workflow
java -jar config-slicer.jar \
    -o validate \
    -s <prod_server> \
    -u <username> \
    -p <password> \
    -k <workflow_name>_workflowManifest.xml \
    > validate_after.out
