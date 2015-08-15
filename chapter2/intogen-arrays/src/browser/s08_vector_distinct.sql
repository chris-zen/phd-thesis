
USE `{browser_db}`;

DROP TABLE IF EXISTS `browser_vector_source_term_root`; 
CREATE TABLE `browser_vector_source_term_root` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `source` (`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `term` (`source_id`,`source_type`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `browser_vector_source_term_root` SELECT DISTINCT v.source_id, v.source_type, v.term_id, v.term_type, 1 AS `module_id`, 6 AS `module_type` FROM browser_vector_source_term_module v;

DROP TABLE IF EXISTS `browser_vector_source_root_module`;
CREATE TABLE `browser_vector_source_root_module` (
  `source_id` int(11) NOT NULL,
  `source_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  PRIMARY KEY (`source_id`,`source_type`,`term_id`,`term_type`,`module_id`,`module_type`),
  KEY `source` (`source_type`,`term_id`,`term_type`,`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `browser_vector_source_root_module` SELECT DISTINCT v.source_id, v.source_type, 1 AS `term_id`, 3 AS `term_type`, v.module_id, v.module_type FROM browser_vector_source_term_module v;

