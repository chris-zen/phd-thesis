# Vectors

USE `{browser_db}`;


# root root module
DROP TABLE IF EXISTS `browser_vector_root_root_module`;
CREATE TABLE `browser_vector_root_root_module` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_gene e;
INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_go e;
INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_kegg e;
INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_mirna e;
INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_onco_comb e;
INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_onco_exp e;
INSERT INTO `browser_vector_root_root_module` SELECT 1 as source_id, 1 as source_type, 1 as term_id, 3 as term_type, e.id as module_id, e.type_id as module_type FROM browser_module_tfbs e;

# root term root
DROP TABLE IF EXISTS `browser_vector_root_term_root`;
CREATE TABLE  `browser_vector_root_term_root` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `term` (`source_id`,`source_type`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_vector_root_term_root` SELECT 1 as source_id, 1 as source_type, e.id as term_id, e.type_id as term_type, 1 as module_id, 6 as module_type FROM browser_term_topography e;
INSERT INTO `browser_vector_root_term_root` SELECT 1 as source_id, 1 as source_type, e.id as term_id, e.type_id as term_type, 1 as module_id, 6 as module_type FROM browser_term_topography_morphology e;

# source root root
DROP TABLE IF EXISTS `browser_vector_source_root_root`;
CREATE TABLE `browser_vector_source_root_root` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `source` (`source_type`,`term_id`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_vector_source_root_root` SELECT e.id as source_id, e.type_id as source_type, 1 as term_id, 3 as term_type, 1 as module_id, 6 as module_type FROM browser_source_experiment_platform e;
