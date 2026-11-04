glims_folder=
clarity_epp=

. $clarity_epp/venv/bin/activate
for file in $glims_folder/*.csv ; do
    if [ -f $file ] ; then
        python -W ignore $clarity_epp/clarity_epp.py upload glims $file
        mv $file $helix_folder/processed
    fi
done
