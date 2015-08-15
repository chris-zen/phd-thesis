To import data from FATHMM:

1) Download the database and the script:

	wget ftp://supfam2.cs.bris.ac.uk/FATHMM/database/fathmm-v2.3.SQL.gz
	wget https://github.com/HAShihab/fathmm/raw/master/cgi-bin/fathmm.py

	echo "CREATE SCHEMA IF NOT EXISTS fathmm" | mysql
	zcat fathmm-v2.3.SQL.gz | mysql -p fathmm

2) Fetch FATHMM scores for all the database:

	mkdir -p byprotein/{snvs,fathmm,scores}
	fannsdb-export -c protein,aa_ref,aa_pos,aa_alt fanns.db - | tail -n+2 | awk 'BEGIN{FS="\t";OFS=FS}{print $1,$2$3$4 >>byprotein/snvs/"$1".tsv}'
	find byprotein/snvs -type f | /opt/parallel/bin/parallel --gnu --progress -j 16 python fathmm.py -w CANCER {} - \| gzip -c \>byprotein/fathmm/{/.}.gz

   *fathmm/\*.gz* files will contain raw results from fathmm.py. To extract only the fathmm score the following script is required:

	cat >extract-scores.sh <<EOF
if [ $# -ne 2 ]; then echo "usage: extract-scores <src> <dst>"; exit -1; fi
zcat $1 | cut -s -f 3,4,6 | awk 'BEGIN{FS="\t";OFS=FS}(NR==1){print "PROTEIN","AA_POS","AA_REF","AA_ALT","FATHMM"}($3!="" && NR>1){print $1,substr($2,2,length($2)-2),substr($2,0,1),substr($2,length($2),1),$3}' | gzip -c >$2
EOF

	find byprotein/fathmm -type f | /opt/parallel/bin/parallel --gnu --progress -j 16 bash ./extract-scores.sh {} byprotein/scores/{/.}.gz

   *scores/\*.gz* files will contain protein, aa_pos, aa_ref, aa_alt and the fathmm score.

3) Import into the database

	find byprotein/scores -type f -exec fannsdb-update -L debug -p FATHMM fanns.db {} \;

