# TransFIC

TransFIC (TRANSformed Functional Impact for Cancer) is a method to transform Functional Impact scores taking into account the differences in basal tolerance to germline SNVs of genes that belong to different functional classes. This transformation allows to use the scores provided by well-known tools (e.g. SIFT, Polyphen2, MutationAssessor) to rank the functional impact of cancer somatic mutations. Mutations with greater transFIC are more likely to be cancer drivers.

## Creation of the baseline tolerance statistics

1) Download The Gene Ontology, get mappings and generate the dependency map tree:

	$ wget http://www.geneontology.org/ontology/obo_format_1_2/gene_ontology.1_2.obo
	$ transfic-obo-to-map --desc --asc --compact gene_ontology.1_2.obo

	$ ensembl-get-ann sep2011.archive.ensembl.org go_ensp_64.map go_id ensembl_peptide_id
	$ ensembl-get-ann sep2011.archive.ensembl.org ensg_prot_64.map ensembl_gene_id ensembl_peptide_id
	$ cat go_ensp_64.map ensg_prot_64.map >>features.map

	$ ensembl-get-ann sep2011.archive.ensembl.org go_ensg_64.map go_id ensembl_gene_id
	$ cat gene_ontology.1_2-desc.map >tree.map
	$ tail -n+5 go_ensg_64.map >>tree.map

**NOTE**: for dbnsfp 2.0 use ensembl 64 at sep2011.archive.ensembl.org

2) Create the list of SNV's for the baseline tolerance:

   For 1000G:

	$ zcat ALL.*.tsv.gz | transfic-vcf-to-snvs -o 1kg.tsv.gz -

   This creates a tsv file like:

	CHR POS    REF ALT
	10  60523  T   G
	10  60969  C   A
	10  61005  A   G

   For ESP6500:

	$ transfic-esp6500-to-snvs ESP6500SI-V2-SSA137.dbSNP138-rsIDs.snps_indels.txt.tar.gz ESP6500.tsv.gz

3) Fetch functional scores:

	$ ensembl-get-ann sep2011.archive.ensembl.org trs_len.tsv ensembl_transcript_id cds_length

	$ zcat 1kg.tsv.gz | tail -n+2 | fannsdb-fetch -a gene -p SIFT,PPH2,MA fanns.db - 1kg-fetch.tsv
	$ transfic-filter-transcripts trs_len.tsv 1kg-fetch.tsv 1kg-fetch-filtered.tsv

	$ zcat ESP6500.tsv.gz | tail -n+2 | fannsdb-fetch -a gene -p SIFT,PPH2,MA,FATHMM fanns.db - esp6500-fetch.tsv
	$ transfic-filter-transcripts trs_len.tsv esp6500-fetch.tsv esp6500-fetch-filtered.tsv

	$ tail -q -n+2 1kg-fetch-filtered.tsv | awk 'BEGIN{FS="\t";OFS="\t";ORS=""}{print $2,$4,$5,$6,$11; for (i=13; i<NF+1; i++) printf("%s%s", OFS, $(i)); printf("\n") }' | sort -u >1kg-scores-prot.tsv

   This generates a file like (CHR, POS, REF, ALT, GENE, SIFT, PPH2, MA):

	10 94599  G A ENSG00000173876 0.0  0.03  2.705
	10 286889 C A ENSG00000015171 0.26 0.003 0.09

   To use transcripts or genes as the feature for statistics filter the fetch.tsv with those commands:

	$ tail -q -n+2 1kg-fetch.tsv | awk 'BEGIN{FS="\t"; OFS="\t"; ORS=""}{print $2,$4,$5,$6,$12; for (i=13; i<NF+1; i++) printf("%s%s", OFS, $(i)); printf("\n") }' | sort -u >1kg-scores-gene.tsv
	$ tail -q -n+2 1kg-fetch.tsv | awk 'BEGIN{FS="\t";OFS="\t";ORS=""}{print $2,$4,$5,$6,$7; for (i=13; i<NF+1; i++) printf("%s%s", OFS, $(i)); printf("\n") }' | sort -u >1kg-scores-trs.tsv

4) Calculate partial baseline tolerance statistics (N, s1, s2):

	$ transfic-blt-partial -t "SIFT=max(1e-2,min(1-1e-2,x))" -t "SIFT=log((1-x)/x)" -t "PPH2=max(1e-3,min(1-1e-3,x))" -t "PPH2=log(x/(1-x))" 1kg-scores-prot.tsv SIFT,PPH2,MA blt-partial.tsv

   The results look like:

	FEATURE          SIFT                            PPH2                             MA
	ENSG00000000005  4/18.3804794005/84.4605057484   4/-110.524084464/3053.89331164   4/3.35/5.20865
	ENSG00000000457  25/114.877996253/527.878160928  25/-690.775527898/19086.8331977  25/34.735/58.500775

5) Calculate baseline tolerance statistics (N, mean, sd):

	$ transfic-blt-groups tree.map GO:0003674 features.map blt-partial.tsv blt-proteins.json

   You can also generate a tsv file like the following example adding the --tsv file.tsv:

	FEATURE	        SIFT                                          PPH2                                           MA
	ENSP00000245441	GO:0005525/L/466/1.95729692703/2.5700670343   GO:0005525/L/394/-1.06199211213/4.16060156178  GO:0005525/L/456/1.51242324561/1.31740712483
	ENSP00000391545	GO:0008270/L/4805/1.60284368781/2.42757705678 GO:0008270/L/4146/-1.53127163636/4.20742908261 GO:0008270/L/4832/1.09480028974/1.11200011804
	ENSP00000391546	GO:0052742/D/68/1.66936429932/2.37031398462   GO:0052742/D/61/-2.19367026523/3.62973578001   GO:0016773/L/104/1.04923076923/1.10998595487

## Calculate TransFIC scores for the whole database

1) Calculate the scores

	$ transfic-calc -p SIFT,PPH2,MA \
	                -t "SIFT=max(1e-2,min(1-1e-2,x))" -t "SIFT=log((1-x)/x)" \
		            -t "PPH2=max(1e-3,min(1-1e-3,x))" -t "PPH2=log(x/(1-x))" fanns.db protein blt-proteins.tsv

   Replace *protein* by *gene* or *transcript* to use baseline tolerance statistics calculated for these other features.

   Update predictors:

	$ fannsdb-pred-update -p TFIC_SIFT,TFIC_PPH2,TFIC_MA fanns.db
	$ fannsdb-pred-list --json fanns.db >pred-list.json

## TransFIC performance

1) Prepare the validation files:

	$ transfic-perf-init

2) Check TransFIC performance

	export DB_PATH=../fanns.db
	export PREDICTORS=SIFT,PPH2,MA,FATHMMC,TFIC_SIFT,TFIC_PPH2,TFIC_MA,TFIC_FATHMMC

   Retrieve the scores for the datasets:

   	$ find snvs -type f -print -exec fannsdb-fetch -p $PREDICTORS -a prot_gene,swissprot_id,swissprot_acc $DB_PATH {} scores/$(basename {})

	$ while read d; do transfic-perf-scores fanns.db SIFT,PPH2,MA,TFIC_SIFT,TFIC_PPH2,TFIC_MA $d; done <datasets.txt | tee perf-scores.txt

   Calculate the MCC:

	$ find scores-filt -type f -exec condel-weights -p SIFT,PPH2,MA,TFIC_SIFT,TFIC_PPH2,TFIC_MA -P 2 -f pred-list.json {} \;

   Plot performance:

	$ transfic-perf-plot -i -c SIFT/TFIC_SIFT -c PPH2/TFIC_PPH2 -c MA/TFIC_MA *-weights.json
	$ transfic-perf-plot -o TransFIC.png -c SIFT/TFIC_SIFT -c PPH2/TFIC_PPH2 -c MA/TFIC_MA *-weights.json


## Calculate cutoffs

1) Calculate cutoffs

	$ transfic-cutoffs -L debug -p TFIC_SIFT,TFIC_PPH2,TFIC_MA -P 2 pred-list.json validation/scores/cosmic-5__cosmic-1
	$ transfic-cutoffs-plot -L debug -i -p TFIC_SIFT,TFIC_PPH2,TFIC_MA cosmic-5__cosmic-1-cutoffs.json
	$ transfic-cutoffs-plot -L debug -o cutoffs.png -p TFIC_SIFT,TFIC_PPH2,TFIC_MA cosmic-5__cosmic-1-cutoffs.json

2) Update the database

	$ transfic-calc-label -L debug -p TFIC_SIFT,TFIC_PPH2,TFIC_MA fanns.db cosmic-5__cosmic-1-cutoffs.json

## Notes about performance datasets

	$ wget ftp://ftp.sanger.ac.uk/pub/CGP/cosmic/data_export/CosmicMutantExport_v67_241013.tsv.gz

	$ transfic-perf-cosmic -L debug -p SIFT fanns.db CosmicMutantExport_v67_241013.tsv cgc_genes.tsv