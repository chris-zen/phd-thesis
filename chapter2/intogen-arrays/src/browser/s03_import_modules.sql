# Import all the modules

USE `{browser_db}`;

# Genes 
DROP TABLE IF EXISTS `browser_module_gene`;
CREATE TABLE `browser_module_gene` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `ensembl` varchar(128) NOT NULL,
  `symbol` varchar(48) DEFAULT NULL,
  `chromosome` varchar(10) DEFAULT NULL,
  `band` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`),
  KEY `ensembl` (`ensembl`),
  KEY `symbol` (`symbol`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_module_gene` SELECT e.id AS id, 7 as type_id, gene_name as ensembl, gene_sym as symbol, gene_chr as chromosome, gene_band as band FROM {biomart_db}.ent_gene e;

# GO
DROP TABLE IF EXISTS `browser_module_go`;
CREATE TABLE  `browser_module_go` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `name` varchar(128) DEFAULT NULL,
  `description` varchar(4096) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_module_go` SELECT e.go_id as id, IF(e.go_ontology='bp',9,IF(e.go_ontology='mf',10,11)) as type_id, e.go_name as name, e.go_desc as description FROM {biomart_db}.ent_go e;

# KEGG
DROP TABLE IF EXISTS `browser_module_kegg`;
CREATE TABLE `browser_module_kegg` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `name` varchar(128) DEFAULT NULL,
  `description` varchar(4096) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_module_kegg` SELECT e.kegg_id as id, 8 as type_id, e.kegg_name as name, e.kegg_desc as description FROM {biomart_db}.ent_kegg e;

# MIRNA
DROP TABLE IF EXISTS `browser_module_mirna`;
CREATE TABLE `browser_module_mirna` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `name` varchar(128) CHARACTER SET latin1 COLLATE latin1_general_cs DEFAULT NULL,
  `mirna_accession` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_module_mirna` SELECT e.mirna_id as id, 13 as type_id, e.mirna_name as name, e.mirna_accession as mirna_accession FROM {biomart_db}.ent_mirna e;

# Onco COMB
DROP TABLE IF EXISTS `browser_module_onco_comb`;
CREATE TABLE `browser_module_onco_comb` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `condition` varchar(30) NOT NULL,
  `topography` varchar(255) NOT NULL,
  `morphology` varchar(255) DEFAULT NULL,
  `caption` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
#TODO Insert

# Onco EXP
DROP TABLE IF EXISTS `browser_module_onco_exp`;
CREATE TABLE `browser_module_onco_exp` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `condition` varchar(30) NOT NULL,
  `topography` varchar(255) NOT NULL,
  `morphology` varchar(255) DEFAULT NULL,
  `platform` varchar(250) NOT NULL,
  `authors` varchar(260) NOT NULL,
  `caption` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
#TODO Insert

# TFBS
DROP TABLE IF EXISTS `browser_module_tfbs`;
CREATE TABLE `browser_module_tfbs` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `description` varchar(4096) DEFAULT NULL,
  `matrix_id` varchar(50) DEFAULT NULL,
  `binding_factor_name` varchar(120) DEFAULT NULL,
  `short_factor_description` varchar(120) DEFAULT NULL,
  `encoding_gene_symbol` varchar(120) DEFAULT NULL,
  `medline_id` varchar(4096) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_module_tfbs` SELECT e.tfbs_id as id, 12 as type_id, e.tfbs_name as name, e.tfbs_desc as description, e.tfbs_matrix as matrix_id, e.tfbs_binding_factor as binding_factor_name, e.tfbs_factor_desc as short_factor_description, e.tfbs_encoding_gene_sym as encoding_gene_symbol, e.tfbs_medline as medline_id FROM {biomart_db}.ent_tfbs e;

# Experiments
DROP TABLE IF EXISTS `browser_source_experiment_platform`;
CREATE TABLE `browser_source_experiment_platform` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type_id` int(11) NOT NULL,
  `caption` varchar(100) DEFAULT NULL,
  `authors` varchar(260) DEFAULT NULL,
  `title` varchar(300) DEFAULT NULL,
  `year` varchar(16) DEFAULT NULL,
  `pubmed` varchar(32) DEFAULT NULL,
  `journal` varchar(200) DEFAULT NULL,
  `database` varchar(128) DEFAULT NULL,
  `ref` varchar(128) DEFAULT NULL,
  `type` varchar(24) DEFAULT NULL,
  `platform` varchar(250) DEFAULT NULL,
  `technology` varchar(96) DEFAULT NULL,
  `platform_id` int(11) DEFAULT NULL,
  `experiment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=489 DEFAULT CHARSET=latin1;
INSERT INTO `browser_source_experiment_platform` SELECT e.id as id, 2 as type_id, CONCAT(SUBSTRING(e.platf_title,1,INSTR(CONCAT(e.platf_title,' '),' ')-1),' / ', SUBSTRING(REPLACE(e.pub_authors,'et al',''),1,20)) AS `caption`, e.pub_authors as authors, e.pub_title as title, e.pub_year as year, e.pub_pubmed as pubmed, e.pub_journal as journal, SUBSTRING(e.study_id,1,INSTR(e.study_id,'-')-1) as `database`, SUBSTRING(e.study_id,INSTR(e.study_id,'-')+1) as ref, IF(e.platf_title='CGH', 'genomic', IF(e.platf_title='aCGH', 'genomic', 'RNA')) as `type`, e.platf_title as platform, e.platf_technology as technology, null as platform_id, null as experiment_id FROM {biomart_db}.ent_experiment e;

# Topography
DROP TABLE IF EXISTS `browser_term_topography`;
CREATE TABLE `browser_term_topography` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `topography` varchar(255) NOT NULL,
  `topography_entry_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_term_topography` SELECT e.id as id, 4 as type_id, e.icdo_topography as topography, null as topography_entry_id FROM {biomart_db}.ent_icdo e WHERE e.icdo_morphology = 'ANY morphology';

# Topography + Morphology
DROP TABLE IF EXISTS `browser_term_topography_morphology`; 
CREATE TABLE `browser_term_topography_morphology` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `topography` varchar(255) NOT NULL,
  `morphology` varchar(255) NOT NULL,
  `topography_entry_id` int(11) DEFAULT NULL,
  `morphology_entry_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_term_topography_morphology` SELECT e.id as id, 5 as type_id, e.icdo_topography as topography, e.icdo_morphology as morphology, null as topography_entry_id, null as morphology_entry_id FROM {biomart_db}.ent_icdo e WHERE e.icdo_morphology <> 'ANY morphology';

