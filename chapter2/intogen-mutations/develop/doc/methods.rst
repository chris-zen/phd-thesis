Methods
=======

We here first introduce the main concepts behind the methods used in IntOGen Mutations analyses.

Identification of mutation consequences and Functional Impact scores
--------------------------------------------------------------------

The first step in the analysis consists on the identification of the effect that mutations may have on transcripts and regulatory regions. For the identification of consequence types of variants originally identified by the mutation project we rely on the Ensembl Variation database via the `Variant Effect Predictor <http://www.ensembl.org/index.html>`_ (VEP). The VEP maps each mutation to the reference genome and identifies each Ensemble transcript that overlaps the variation. Using a rule-based approach, VEP predicts the effect that each mutation may have on the transcript. The output is a list of consequence terms, defined by the Sequence Ontology (SO), for each mutation and transcript. For a definition of each term look at the table in `VEP documentation <http://www.ensembl.org/info/docs/variation/predicted_data.html#consequences>`_.

Then, the pipeline queries the `MutationAssessor <http://mutationassessor.org/>`_ data to obtain MutationAssessor Functional Impact scores of variants with non-synonymous consequence types.

Assessment of functional impact of mutations
--------------------------------------------

Non-synonymous variants (nsSNVs) are variants that change one amino acid in a protein. The effect that this amino acid change may have on the function of the protein depends on multiple factors, and may range from almost no impact (i.e. the protein can function well with this amino acid change) to very high functional impact (i.e. the protein is not functional). There are numerous computational methods to assess the functional impact of nsSNVs, although most were originally developed to distinguish disease-related non-synonymous single nucleotide variants (nsSNVs) from polymorphisms.

As mentioned in the previous section, we use three well-known tools (*SIFT*, *PolyPhen2* and *MutationAssessor*) to compute the Functional Impact scores of somatic mutations detected across tumor samples. Each Functional Impact score is transformed using the `TransFIC <http://bg.upf.edu/transfic>`_ approach recently developed by us, which compares the original score provided by the tool to the distribution of scores of SNVs observed in the germline of human populations in genes that are similar to the one bearing the mutation. We have called this distribution "basal tolerance" of the genes, and we have computed it for small pools of genes related to one another by their molecular function (obtained from the `Gene Ontologies Molecular Functions database <http://www.geneontology.org/>`_).

Based on the *TransFIC* score of each mutation, the pipeline classifies them into one of four discrete groups, intended to broadly describe their impact on the protein product of the gene where it occurs. These groups are defined using a simple rule-based approach and the distribution of highly-recurrent and non-recurrent `Cosmic <http://cancer.sanger.ac.uk/cancergenome/projects/cosmic/>`_ mutations.

According to this classification, a variant may be assigned one of the following impacts:

* **None**: if it doesn’t affect the protein sequence, either because it overlaps only non-coding regions of the transcripts, or because it only produces synonymous consequence types.
* **Low**: if it is a non-synonymous mutation with low *MA* *TransFIC*
* **Medium**: if it is a non-synonymous mutation with medium *MA* *TransFIC*
* **High**: if it is a non-synonymous mutation with high *MA* *TransFIC*, or a stop mutation or a frameshift-causing indel

Identification of drivers using functional impact bias (OncodriveFM)
--------------------------------------------------------------------

Genes
'''''

To identify driver genes from mutations in a cohort of tumors we use `OncodriveFM <https://bitbucket.org/bbglab/oncodrivefm>`_. This method is based on the assumption that cancer driver genes accumulate highly functional mutations, as those are the ones that alter the function of the encoded protein, conferring a selective advantage to the cell. Oncodrive-fm computes a metric called FM-bias, which measures the bias towards the accumulation of functional mutations. Genes with a high FM-bias are candidate drivers.

The FM bias of each gene is measured as the deviation of the accumulated mutations’ functional impact on the gene with respect to a null distribution. The aim is to detect how many more functional mutations the gene accumulates across all samples than the average gene, which is not subjected to positive selection during tumor development. If all genes in the cancer genome have been sequenced across a sufficient number of samples, OncodriveFM models the accumulated mutational burden of this average gene as a null distribution composed of one million vectors of mutations randomly sampled from the mutation matrix produced by the project. These vectors have the same dimensionality as the number of variants originally detected in the gene under analysis. For example, if a gene is mutated in 10 tumor samples, one million groups of 10 mutations are randomly selected from the list of mutations found in the tumor samples. We call this the internal null distribution and it should be used in the execution of the pipeline to assess the FM bias of genes if these two conditions are met: i) all genes in the cancer genome have been sequenced, and ii) a sufficient number of samples (from our experience, we recommend at least 40) has been analyzed.

If any of these two conditions is not met, the FM bias should be computed using the external null distribution, which compares the mutational accumulated Functional Impact of the gene to the distribution of germline SNVs observed in the human population on genes with similar functional characteristics.

Pathways
''''''''

To identify driver pathways we also use Oncodrive-fm. In this case, instead of computing an FM-bias per gene we compute it per each KEGG pathway. Pathways with a high FM-bias are candidate drivers.

Identification of drivers using regional clustering (OncodriveCLUST)
--------------------------------------------------------------------

.. todo::

   include a section for OncodriveCLUST

Recurrence analysis per mutation, gene and pathway
--------------------------------------------------

A common, straight-forward measure to assess the importance of mutations is the frequency in which each gene or pathway is mutated in a cohort of tumors. Within the IntOGen-Mutations pipeline we have included the computation of a very simple metric of mutational recurrence.

A) The **recurrence of each individual mutation** identified by the original mutation project is computed by counting the number of tumor samples where it appears. We call this metric total_samples.

B) To compute the **mutational frequency of each gene**, the pipeline counts the number of samples where it is found mutated and divides it by the total number of samples.

C) Finally, three separate metrics are computed to assess the **mutational frequency of each pathway**. First, the pipeline counts the number of samples where mutations in a gene within the pathway were identified. (If two genes of the pathway are mutated in the same sample, they contribute two mutations to the metric). Second, the pipeline counts the number of non-redundant samples where mutations in a gene within the pathway were identified. Finally, a gene-based mutational frequency of the pathway is obtained by dividing the recurrence metric by the total number of samples analyzed by the project and by the number of genes included in the pathway, thus normalizing the recurrence by pathway size.
