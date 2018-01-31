helix_folder=
clarity_epp=

. $clarity_epp/venv/bin/activate
for file in $helix_folder/*.csv ; do
    if [ -f $file ] ; then
        python $clarity_epp/clarity_epp.py upload sample $file
        mv $file $helix_folder/processed
    fi
done
