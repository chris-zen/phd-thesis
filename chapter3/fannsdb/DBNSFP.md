To import data from [dbNSFP](https://sites.google.com/site/jpopgen/dbNSFP):

1) Download the database:

	wget http://dbnsfp.houstonbioinformatics.org/dbNSFPzip/dbNSFP2.0.zip
	wget http://dbnsfp.houstonbioinformatics.org/dbNSFPzip/dbNSFPv2.1.zip

2) Export into files splited by chromosome:

	(seq 1 22; echo X; echo Y) | parallel --gnu --progress dbnsfp-export -o dbnsfp-{}.tsv.gz -O dbnsfp-{}-noprot.vcf --chr {} dbNSFP2.0.zip ensp_enst.map ensp_uniprot.map 2\>dbnsfp-{}.log

	*ensp_enst.map* and *ensp_uniprot.map* can be retrieved with the script *bin/get-dbnsfp-prot-map*

3) Import into fanns database:

	for i in $(seq 1 22; echo X; echo Y); do echo "Importing chromosome $i ..."; zcat dbnsfp-$i.tsv.gz | fannsdb-import -L debug -p SIFT,PPH2,MA --skip-empty-scores --skip-create-index --skip-update-predictors fanns.db -; done
	fannsdb-pred-update -p SIFT,PPH2,MA fanns.db
	fannsdb-index fanns.db create

4) Fix dbsnfp 2.0 errors:

	sqlite3 fanns.db
	update scores set SIFT=NULL where protein_id=(select protein_id from id_protein where protein_name='ENSP00000363197') and prot_code=121057;
	update scores set SIFT=0.66 where protein_id=(select protein_id from id_protein where protein_name='ENSP00000444545') and prot_code=188641;
	update scores set SIFT=0.59 where protein_id=(select protein_id from id_protein where protein_name='ENSP00000402565') and prot_code=116961;
	update scores set SIFT=0.0 where protein_id=(select protein_id from id_protein where protein_name='ENSP00000329576') and prot_code=89313;
	update scores set SIFT=0.0 where protein_id=(select protein_id from id_protein where protein_name='ENSP00000363900') and prot_code=182497;
	update scores set SIFT=0.12 where protein_id=(select protein_id from id_protein where protein_name='ENSP00000438774') and prot_code=87265;
	update scores set SIFT=NULL where protein_id=(select protein_id from id_protein where protein_name='ENSP00000422716') and prot_code=235745;

	cat >fix_sift.tsv <<EOF
ENSP00000394210	603	G	R
ENSP00000404438	316	G	R	0.02
ENSP00000431445	27	G	R	0.41
ENSP00000412740	112	G	R	0.1
ENSP00000384691	170	G	R	0.02
ENSP00000343225	260	G	R	0.12
ENSP00000438060	171	G	R	0.29
ENSP00000387982	37	G	R	0.93
ENSP00000383988	106	V	L	0.02
EOF
	fannsdb-update fanns.db fix_sift.tsv -p SIFT -L debug


**To check errors:**

	$ for i in $(seq 1 22; echo X; echo Y); do zcat /shared/datasets/dbNSFP/2.0/parsed-2/dbnsfp-$i.tsv.gz | awk -f check_sift.awk; done | tee check_sift.log

	ERROR at        4368817 :
	1       -       27480474        C       G       ENST00000374084 118     G       R       ENSP00000363197 0.02    0.996   2.01    -0.24
	1       -       27480474        C       T       ENST00000374084 118     G       R       ENSP00000363197 0.0             1.94

	ERROR at        8115437 :
	1       -       51204536        C       G       ENST00000543607 184     G       R       ENSP00000444545 0.46    0.068   0.0     -1.07
	1       -       51204536        C       T       ENST00000543607 184     G       R       ENSP00000444545 0.66            -1.39

	ERROR at        14656399        :
	1       -       152383218       C       G       ENST00000451038 114     G       R       ENSP00000402565 0.16    0.005   1.83    3.57
	1       -       152383218       C       T       ENST00000451038 114     G       R       ENSP00000402565 0.59            1.83

	There were      3       errors
	There were      0       errors
	There were      0       errors
	ERROR at        7380223 :
	4       -       129208687       C       G       ENST00000332709 87      G       R       ENSP00000329576 0.48    0.421   1.445   -1.67
	4       -       129208687       C       T       ENST00000332709 87      G       R       ENSP00000329576 0.0             1.445

	There were      1       errors
	There were      0       errors
	There were      0       errors
	There were      0       errors
	There were      0       errors
	ERROR at        9133002 :
	9       -       136561345       C       G       ENST00000427237 603     G       R       ENSP00000394210 0.0     0.979   3.475   -2.21
	9       -       136561345       C       T       ENST00000427237 603     G       R       ENSP00000394210 0.02            3.13    -2.21

	ERROR at        9295596 :
	9       -       138586233       C       G       ENST00000425225 316     G       R       ENSP00000404438 0.0     0.998           -0.78
	9       -       138586233       C       T       ENST00000425225 316     G       R       ENSP00000404438 0.02    0.999           0.3

	There were      2       errors
	ERROR at        2322725 :
	10      -       34636893        C       G       ENST00000374768 178     G       R       ENSP00000363900 0.22            1.795   1.89
	10      -       34636893        C       T       ENST00000374768 178     G       R       ENSP00000363900 0.0             1.795   1.89

	ERROR at        6768891 :
	10      +       96961258        G       A       ENST00000539707 85      G       R       ENSP00000438774 0.12
	10      +       96961258        G       C       ENST00000539707 85      G       R       ENSP00000438774 0.0

	There were      2       errors
	ERROR at        13389191        :
	11      +       118219765       G       A       ENST00000532917 27      G       R       ENSP00000431445 0.41    0.312   1.59    1.11
	11      +       118219765       G       C       ENST00000532917 27      G       R       ENSP00000431445 0.0     0.312   1.59    1.11

	There were      1       errors
	ERROR at        2172544 :
	12      -       11461583        C       G       ENST00000445719 112     G       R       ENSP00000412740 0.09    0.887   1.39    2.91
	12      -       11461583        C       T       ENST00000445719 112     G       R       ENSP00000412740 0.1             0.84    2.91

	ERROR at        4870990 :
	12      -       49361932        C       G       ENST00000407467 170     G       R       ENSP00000384691 0.01    0.917   1.655   -2.6
	12      -       49361932        C       T       ENST00000407467 170     G       R       ENSP00000384691 0.02    0.123   1.31    -2.6

	ERROR at        9098429 :
	12      -       77419586        C       G       ENST00000339887 260     G       R       ENSP00000343225 0.49            0.895   2.45
	12      -       77419586        C       T       ENST00000339887 260     G       R       ENSP00000343225 0.12            0.55

	ERROR at        13564298        :
	12      -       124110973       C       G       ENST00000539951 171     G       R       ENSP00000438060 0.25    1.0     2.475   -3.57
	12      -       124110973       C       T       ENST00000539951 171     G       R       ENSP00000438060 0.29            1.835   -3.57

	There were      4       errors
	There were      0       errors
	There were      0       errors
	ERROR at        5604978 :
	15      -       85196863        C       G       ENST00000434634 37      G       R       ENSP00000387982 0.27    1.0     1.61    0.65
	15      -       85196863        C       T       ENST00000434634 37      G       R       ENSP00000387982 0.93    1.0     1.61    0.65

	There were      1       errors
	There were      0       errors
	There were      0       errors
	There were      0       errors
	ERROR at        5845780 :
	19      -       36497504        C       G       ENST00000490730 230     G       R       ENSP00000422716 0.08    0.796   1.04    0.59
	19      -       36497504        C       T       ENST00000490730 230     G       R       ENSP00000422716 0.3     0.027   0.695   0.59

	There were      1       errors
	There were      0       errors
	There were      0       errors
	There were      0       errors
	ERROR at        9027822 :
	X       -       153706623       C       A       ENST00000407062 106     V       L       ENSP00000383988 0.02            2.93    1.5
	X       -       153706623       C       G       ENST00000407062 106     V       L       ENSP00000383988 0.09    0.201   2.24    1.5

	There were      1       errors
	There were      0       errors

**check_sift.awk**

	BEGIN {
	  FS="\t"
	  OFS=FS
	  L=""
	  P=""
	  S=""
	  E=0
	}

	{
	  CP=$10 " " $8 $7 $9
	  CS=$11
	  if (CP != P) {
		if (length(CS) > 0) {
		  L=$0 "\n"
		  P=CP
		  S=CS
		}
		else {
		  L=""
		  P=""
		  S=""
		}
	  }
	  else {
		if ($9 != "X" && length(CS) > 0) {
		  L = L $0 "\n"
		  if (CS != S) {
			E = E + 1
			print "ERROR at ",NR,":"
			print L
		  }
		}
	  }
	}

	END {
	  print "There were ",E,"errors"
	}
