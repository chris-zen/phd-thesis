
# Create user tables

USE `{browser_db}`;

DROP TABLE IF EXISTS `browser_user_entities`;
CREATE TABLE  `browser_user_entities` (
  `id` int(11) NOT NULL,
  `type_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id`,`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `browser_user_maps`;
CREATE TABLE  `browser_user_maps` (
  `parent_id` int(11) NOT NULL,
  `parent_type` int(11) NOT NULL,
  `child_id` int(11) NOT NULL,
  `child_type` int(11) NOT NULL,
  KEY `parent` (`parent_id`,`parent_type`,`child_type`),
  KEY `all` (`parent_id`,`parent_type`,`child_id`,`child_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `browser_user_type_properties`;
CREATE TABLE `browser_user_type_properties` (
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

DROP TABLE IF EXISTS `browser_user_types`;
CREATE TABLE `browser_user_types` (
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
  `token` varchar(30) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

