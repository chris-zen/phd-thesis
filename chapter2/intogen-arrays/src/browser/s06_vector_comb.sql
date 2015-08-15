# Vectors

USE `{browser_db}`;

# Combinations
# browser_vector_root_term_module

DROP TABLE IF EXISTS `browser_vector_root_term_module`;
CREATE TABLE  `browser_vector_root_term_module` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  `upreg` double DEFAULT NULL,
  `downreg` double DEFAULT NULL,
  `gain` double DEFAULT NULL,
  `loss` double DEFAULT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `term` (`source_id`,`source_type`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# Copy CNA

# genes 
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, v.gene_id as module_id, 7 as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_gene_cna v JOIN browser_term_topography t ON t.id=v.icdo_id;
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, v.gene_id as module_id, 7 as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_gene_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id;

# go
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_go_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id;
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_go_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id;

# kegg
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_kegg_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id;
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_kegg_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id;

# mirna
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_mirna_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id;
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_mirna_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id;

# tfbs
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_tfbs_cna v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id;
INSERT INTO `browser_vector_root_term_module` SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, null as upreg, null as downreg, v.gain_pvalue as gain, v.loss_pvalue as loss FROM {biomart_db}.cmb_tfbs_cna v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id;

# Transcriptomic

# genes
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, v.gene_id as module_id, 7 as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_gene_trs v JOIN browser_term_topography t ON t.id=v.icdo_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, v.gene_id as module_id, 7 as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_gene_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;

# go
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_go_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_go_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_go m ON m.id=v.go_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;

# kegg
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_kegg_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_kegg_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_kegg m ON m.id=v.kegg_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;

# mirna
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_mirna_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_mirna_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_mirna m ON m.id=v.mirna_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;

# tfbs
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_tfbs_trs v JOIN browser_term_topography t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;
INSERT INTO `browser_vector_root_term_module` (source_id, source_type, term_id, term_type, module_id, module_type, upreg, downreg) SELECT 1 as source_id, 1 as source_type, t.id as term_id, t.type_id as term_type, m.id as module_id, m.type_id as module_type, v.upreg_pvalue as upreg, v.downreg_pvalue as downreg FROM {biomart_db}.cmb_tfbs_trs v JOIN browser_term_topography_morphology t ON t.id=v.icdo_id JOIN browser_module_tfbs m ON m.id=v.tfbs_id ON DUPLICATE KEY UPDATE upreg=v.upreg_pvalue, downreg=v.downreg_pvalue;



