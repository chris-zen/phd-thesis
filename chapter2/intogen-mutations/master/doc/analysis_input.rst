Input files
===========

To run the pipeline you need to input a catalog of mutations from a cohort of tumors. The input can be provided in three different formats (Tabulated, VCF and MAF). Additionally, you can provide an annotation file with clinical features of the samples, which will be used when exploring the results in the browser.

Tabulated format
----------------

The default format (when the file extension is neither *.vcf* or *.maf*) is a simple tab-separated format, containing six required columns:

* **chromosome**: just the name or number, with or without the 'chr' prefix.
* **start**: start and end are reversed in the case of insertions.
* **end**
* **strand**: defined as + (forward) or - (reverse) (+1, 1, -1 are also allowed).
* **allele**: pair of alleles as REF>ALT, where REF is the reference nucleotide and ALT the alternative allele found. REF and ALT can be ‘-’ to express insertion or deletion.
* **sample_id**: Identifier of the sample.

Example::

	X	37901198	37901198	-	C>T		TCGA-AB-2927-03A-01W-0755-09
	X	39817029	39817028	+	->G		TCGA-AB-2968-03A-01D-0739-09
	X	39818802	39818802	-	C>-		TCGA-AB-2970-03A-01D-0739-09
	X	74674244	74674244	-	T>G		TCGA-AB-2807-03D-01W-0755-09
	X	101025404	101025407	+	CTTT>-		TCGA-AB-2911-03A-01W-0732-08
	1	15391333	15391332	+	->AGCGTAAG	TCGA-AB-2982-03A-01D-0739-09
	X	101025404	101025407	-	CTTT>-		TCGA-AB-2911-03A-01W-0732-08

IntOGen Mutations accepts both *hg18* and *hg19* coordinates. The genomic coordinates system can be specified at the beginning of the pipeline; otherwise, it will assume the default *hg19*.

Variant Call Format (VCF)
-------------------------

*VCF* is a text file format for storing and reporting genomic sequence variations. IntOGen Mutations accepts this format in one or many files. Each sample can be identified by adding the header *"##INDIVIDUAL=sample_id"* before each sample’s data.

You will find more information on this format in the following links:

* `TCGA VCF <https://wiki.nci.nih.gov/display/TCGA/TCGA+Variant+Call+Format+%28VCF%29+Specification#TCGAVariantCallFormatVCF11Specification-AboutTCGAVCFspecification>`_
* `VCF 4.1 <http://www.1000genomes.org/wiki/Analysis/Variant%20Call%20Format/vcf-variant-call-format-version-41>`_

Mutation Annotation Format (MAF)
--------------------------------

The *MAF* format is tab-separated plain text. The file may contain many columns, as it can be seen in the specification; however, the only columns that are necessary for IntOGen Mutations are:

* Chrom
* Start_Position
* End_Position
* Strand
* Tumor_Seq_Allele1
* Tumor_Seq_Allele2
* Tumor_Sample_Barcode

You will find more information on the folloging link:

* `Mutation Annotation Format (MAF) Specification <https://wiki.nci.nih.gov/display/TCGA/Mutation+Annotation+Format+%28MAF%29+Specification>`_

Compressed files
----------------

Files in any of the previous formats may be packaged in any of the following compressed formats:

* Gzip
* Bzip2
* Zip
* Tar
* Tar.gz
