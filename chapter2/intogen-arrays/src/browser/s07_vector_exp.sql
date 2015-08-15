# Vectors

USE `{browser_db}`;

DROP TABLE IF EXISTS `browser_vector_source_term_module`;
CREATE TABLE  `browser_vector_source_term_module` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  `upreg_mean` double DEFAULT NULL,
  `upreg_n` int(11) DEFAULT NULL,
  `upreg_observed` double DEFAULT NULL,
  `upreg_pvalue` double DEFAULT NULL,
  `upreg_qvalue` double DEFAULT NULL,
  `upreg_stdev` double DEFAULT NULL,
  `downreg_mean` double DEFAULT NULL,
  `downreg_n` int(11) DEFAULT NULL,
  `downreg_observed` double DEFAULT NULL,
  `downreg_pvalue` double DEFAULT NULL,
  `downreg_qvalue` double DEFAULT NULL,
  `downreg_stdev` double DEFAULT NULL,
  `gain_mean` double DEFAULT NULL,
  `gain_n` int(11) DEFAULT NULL,
  `gain_observed` double DEFAULT NULL,
  `gain_pvalue` double DEFAULT NULL,
  `gain_qvalue` double DEFAULT NULL,
  `gain_stdev` double DEFAULT NULL,
  `loss_mean` double DEFAULT NULL,
  `loss_n` int(11) DEFAULT NULL,
  `loss_observed` double DEFAULT NULL,
  `loss_pvalue` double DEFAULT NULL,
  `loss_qvalue` double DEFAULT NULL,
  `loss_stdev` double DEFAULT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `source` (`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `term` (`source_id`,`source_type`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# CNA

# Gene
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_gene_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_gene m ON m.id=v.gene_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_gene_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_gene m ON m.id=v.gene_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;

# GO
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_go_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_go_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;

# Kegg
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_kegg_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_kegg_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;

# mirna
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_mirna_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_mirna_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;

# tfbs
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_tfbs_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, gain_n, gain_observed, gain_mean, gain_stdev, gain_pvalue, gain_qvalue, loss_n, loss_observed, loss_mean, loss_stdev, loss_pvalue, loss_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.gain_total, v.gain_observed, v.gain_expected, v.gain_stdev, v.gain_pvalue, v.gain_cpvalue, v.loss_total, v.loss_observed, v.loss_expected, v.loss_stdev, v.loss_pvalue, v.loss_cpvalue FROM {biomart_db}.exp_tfbs_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id;

# Transcriptomic

# genes
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_gene_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_gene m ON m.id=v.gene_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_gene_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_gene m ON m.id=v.gene_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;

# GO
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_go_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_go_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;

# KEGG
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_kegg_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_kegg_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;

# mirna
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_mirna_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_mirna_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;

# tfbs
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_tfbs_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;
INSERT INTO `browser_vector_source_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg_n, upreg_observed, upreg_mean, upreg_stdev, upreg_pvalue, upreg_qvalue, downreg_n, downreg_observed, downreg_mean, downreg_stdev, downreg_pvalue, downreg_qvalue) SELECT s.id, s.type_id, t.id, t.type_id, m.id, m.type_id, v.upreg_total, v.upreg_observed, v.upreg_expected, v.upreg_stdev, v.upreg_pvalue, v.upreg_cpvalue, v.downreg_total, v.downreg_observed, v.downreg_expected, v.downreg_stdev, v.downreg_pvalue, v.downreg_cpvalue FROM {biomart_db}.exp_tfbs_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id JOIN browser_source_experiment_platform s ON s.id=v.exp_id ON DUPLICATE KEY UPDATE upreg_n=v.upreg_total, upreg_observed=v.upreg_observed, upreg_mean=v.upreg_expected, upreg_stdev=v.upreg_stdev, upreg_pvalue=v.upreg_pvalue, upreg_qvalue=v.upreg_cpvalue, downreg_n=v.downreg_total, downreg_observed=v.downreg_observed, downreg_mean=v.downreg_expected, downreg_stdev=v.downreg_stdev, downreg_pvalue=v.downreg_pvalue, downreg_qvalue=v.downreg_cpvalue;


