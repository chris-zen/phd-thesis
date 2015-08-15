
# Common tables

USE `{browser_db}`;

DROP TABLE IF EXISTS `browser_types`;
CREATE TABLE  `browser_types` (
  `id` int(11) NOT NULL,
  `type_class` int(11) NOT NULL,
  `key` varchar(255) NOT NULL,
  `label` varchar(255) NOT NULL,
  `description` varchar(255) NOT NULL,
  `sql_table` varchar(50) NOT NULL,
  `dimension` int(11) NOT NULL,
  `sql_vector_suffix` varchar(20) NOT NULL,
  `is_vector_result` tinyint(1) NOT NULL,
  `is_source_result` tinyint(1) NOT NULL,
  `is_term_result` tinyint(1) NOT NULL,
  `is_module_result` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_types` SELECT * FROM browser_010002_06.browser_types b;

DROP TABLE IF EXISTS `browser_type_properties`;
CREATE TABLE `browser_type_properties` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `label` varchar(100) NOT NULL,
  `is_filterable` tinyint(1) NOT NULL,
  `is_searchable` tinyint(1) NOT NULL,
  `is_sortable` tinyint(1) NOT NULL,
  `sql_field` varchar(100) NOT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `browser_type_properties` SELECT * FROM browser_010002_06.browser_type_properties b;

DROP TABLE IF EXISTS `browser_root`;
CREATE TABLE `browser_root` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `label` varchar(30) NOT NULL,
  `description` varchar(100) NOT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_root` SELECT * FROM browser_010002_06.browser_root b;
