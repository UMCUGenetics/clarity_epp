helix_folder=
clarity_epp=

. $clarity_epp/venv/bin/activate
for file in $helix_folder/*.csv ; do
    if [[ "$file" == "WL"*".csv" ]] ; then
        python -W ignore $clarity_epp/clarity_epp.py upload helix $file worklist
        mv $file $helix_folder/processed
    fi
    if [[ "$file" == "dna_mons_indi_tijd"*".csv" ]] ; then
        python -W ignore $clarity_epp/clarity_epp.py upload helix $file sql
        mv $file $helix_folder/processed
    fi
done
