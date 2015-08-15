Results
=======

Currently, the IntOGen Mutations pipeline produces a set of files with the results of all the analyses included within it. These files may be downloaded as a single compressed file upon completion of the execution. They are all tab separated files, which facilitates their exploration. They are roughly organized following the same logic as the IntOGen tabs, and contain exactly the same information. The file names are meant to be descriptive of their contents.

project.tsv
-----------

This file contains information about the project analysed. Basically contains the following fixed fields:

* **PROJECT_ID**: The projectidentifier.
* **ASSEMBLY**: The genome assembly.
* **SAMPLES_TOTAL**: The total number of samples analysed.

There will be also columns representing project annotations in case they were specified.

consequences.tsv
----------------

This file contains information about the transcripts affected by the input mutations. It contains mainly the Variant Effect Predictor results and TransFIC calculations.

* **PROJECT_ID**: The project identifier.
* **CHR**: The mutation's chromosome.
* **STRAND**: The mutations's strand.
* **START**: The mutation's start position.
* **ALLELE**: The mutation's affected nucleotides. The reference and changed sequences are separated by a slash '/'.
* **TRANSCRIPT_ID**: The Ensembl identifier of the transcript affected by the mutation.
* **CT**: The list of Sequence Ontology terms describing the consequence of the mutation.
* **GENE_ID**: The Ensembl identifier of the gene coded by the transcript.
* **SYMBOL**: The HUGO symbol of the gene.
* **UNIPROT_ID**: The Uniprot identifier of the protein.
* **PROTEIN_ID**: The Ensembl identifier of the protein.
* **PROTEIN_POS**: The position of the mutation in protein coordinates.
* **AA_CHANGE**: The aminoacids change separated by a slash '/'.
* **SIFT_SCORE**: SIFT score of the mutation as obtained from VEP (mutations whose consequence types are not prone to affect the sequence of the protein product have empty values).
* **SIFT_TRANSFIC**: The transformed score of SIFT calculated with TransFIC.
* **SIFT_TRANSFIC_CLASS**: Classification of this mutation based on the SIFT TransFIC and its separation of highly-recurrent and non-recurrent somatic mutations in COSMIC.
* **PPH2_SCORE**: Polyphen2 score of the mutation as obtained from VEP (mutations whose consequence types are not prone to affect the sequence of the protein product have empty values).
* **PPH2_TRANSFIC**: The transformed score of Polyphen2 calculated with TransFIC.
* **PPH2_TRANSFIC_CLASS**: Classification of this mutation based on the Polyphen2 TransFIC and its separation of highly-recurrent and non-recurrent somatic mutations in COSMIC.
* **MA_SCORE**: Mutation assessor score of the mutation as obtained from the Mutation assessor database (mutations whose consequence types are not prone to affect the sequence of the protein product have empty values).
* **MA_TRANSFIC**: The transformed score of MA calculated with TransFIC.
* **MA_TRANSFIC_CLASS**: Classification of this mutation based on the MA TransFIC and its separation of highly-recurrent and non-recurrent somatic mutations in COSMIC.
* **IMPACT**: assessment of the functional impact of the mutation on the transcript. The possible values that can take are: (4) mutation that doesn’t affect the protein sequence, (3) non-synonymous mutation with low MA TransFIC, (2) non-synonymous mutation with medium MA TransFIC, (1) non-synonymous mutations with high MA TransFIC, stop mutation or frameshift causing indel.
* **IMPACT_CLASS**: Classification label for the impact: (4) none, (3) low, (2) medium, (1) high.

variant_genes.tsv
-----------------

This file contains information about the mutations affecting genes.

* **PROJECT_ID**: The project identifier.
* **CHR**: The mutation's chromosome.
* **STRAND**: The mutations's strand.
* **START**: The mutation's start position.
* **ALLELE**: The mutation's affected nucleotides. The reference and changed sequences are separated by a slash '/'.
* **GENE_ID**: The Ensembl identifier of the gene coded by the transcript.
* **SYMBOL**: The HUGO symbol of the gene.
* **VAR_IMPACT**: assessment of the functional impact of the mutation on the on the gene. The possible values that can take are: (4) mutation that doesn’t affect the protein sequence, (3) non-synonymous mutation with low MA TransFIC, (2) non-synonymous mutation with medium MA TransFIC, (1) non-synonymous mutations with high MA TransFIC, stop mutation or frameshift causing indel.
* **VAR_IMPACT_CLASS**: Classification label for the impact: (4) none, (3) low, (2) medium, (1) high.
* **SAMPLE_FREQ**: Number of samples where this mutation has been found.
* **SAMPLE_PROP**: Proportion of samples presenting this mutation among the total number of samples.
* **SAMPLE_TOTAL**: The total number of samples analysed.
* **CODING_REGION**: Whether the mutation affects to the coding region of the gene. It will take value 1 when at least one transcript have any of the following consequence terms: missense_variant, stop_gained, stop_lost, frameshift_variant, synonymous_variant, splice_donor_variant, splice_acceptor_variant, splice_region_variant. And 0 otherwise.
* **XREFS**: The comma separated list of external references. When the mutation is known and have an identifier in an external source (such as dbSNP or COSMIC).

variant_samples.tsv
-------------------

This file contains information about the sample identifiers associated with each mutation.

* **PROJECT_ID**: The project identifier.
* **CHR**: The mutation's chromosome.
* **STRAND**: The mutations's strand.
* **START**: The mutation's start position.
* **ALLELE**: The mutation's affected nucleotides. The reference and changed sequences are separated by a slash '/'.
* **SAMPLES**: The comma separated list of samples where this mutation has been found.

genes.tsv
---------

This file contains information for genes.

* **PROJECT_ID**: The project identifier.
* **GENE_ID**: The Ensembl identifier of the gene coded by the transcript.
* **SYMBOL**: The HUGO symbol of the gene.
* **SAMPLE_FREQ**: Number of samples where this gene has been found mutated.
* **SAMPLE_PROP**: Proportion of samples having this gene mutated among the total number of samples.
* **SAMPLE_TOTAL**: The total number of samples analysed.
* **FM_PVALUE**: P-value obtained from the OncodriveFM analysis. Genes with small P-values have a greater likelihood of being drivers.
* **FM_QVALUE**: The OncodriveFM P-value corrected by FDR.
* **FM_EXC_CAUSE**: The reason why this gene has not a resulting p-value from OncodriveFM, where *F*="Excluded by the predefined expression filter", *T*="Number of samples with this gene affected less than the defined threshold"
* **CLUST_ZSCORE**: Z-score obtained from OncodriveCLUST analysis.
* **CLUST_PVALUE**: P-value obtained from OncodriveCLUST analysis.
* **CLUST_QVALUE**: The OncodriveCLUST P-value corrected by FDR.
* **CLUST_COORDS**: The coordinates obtained from OncodriveCLUST analysis.
* **CLUST_EXC_CAUSE**: The reason why this gene has not a resulting p-value from OncodriveCLUST, where *F*="Excluded by the predefined expression filter", *T*="Number of samples with this gene affected less than the defined threshold"
* **INTOGEN_DRIVER**: Whether this gene has been found to be a driver in IntOGen.
* **XREFS**: The comma separated list of external references for the overlapping mutations. When the mutation is known and have an identifier in an external source (such as dbSNP or COSMIC).

pathways.tsv
------------

This file contains information for pathways.

* **PROJECT_ID**: The project identifier.
* **PATHWAY_ID**: The pathway identifier.
* **GENE_COUNT**: Number of genes known to be associated with this pathway.
* **FM_ZSCORE**: Z-score obtained from the OncodriveFM analysis.
* **FM_PVALUE**: P-value obtained from the OncodriveFM analysis. Pathways with small P-values have a greater likelihood of being drivers.
* **FM_QVALUE**: The OncodriveFM P-value corrected by FDR.
* **SAMPLE_FREQ**: Number of samples where this gene has been found mutated.
* **SAMPLE_PROP**: Proportion of samples having this gene mutated among the total number of samples.
* **SAMPLE_TOTAL**: The total number of samples analysed.

fimpact.gitools.tdm
-------------------

This file contains the functional impact matrix for samples and genes. It is in a format that can be opened with `Gitools <www.gitools.org>`_.
