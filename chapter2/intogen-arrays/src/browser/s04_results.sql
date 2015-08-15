# Results load

USE `{browser_db}`;

# CGC
DROP TABLE IF EXISTS `browser_result_cgc`;
CREATE TABLE  `browser_result_cgc` (
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  `csm` varchar(255) DEFAULT NULL,
  `cgm` varchar(255) DEFAULT NULL,
  `ttsm` varchar(255) DEFAULT NULL,
  `ttgm` varchar(255) DEFAULT NULL,
  `cs` varchar(255) DEFAULT NULL,
  `tt` varchar(255) DEFAULT NULL,
  `cmg` varchar(255) DEFAULT NULL,
  `tp` varchar(255) DEFAULT NULL,
  `ogm` varchar(255) DEFAULT NULL,
  `osd` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_result_cgc` SELECT nm.id as module_id, nm.type_id as module_type, r.csm as csm, r.cgm as cgm, r.ttsm as ttsm, r.ttgm as ttgm, r.cs as cs, r.tt as tt, r.cmg as cmg, r.tp as tp, r.ogm as ogm, r.osd as osd FROM browser_010002_06.browser_result_cgc r JOIN browser_010002_06.browser_module_gene m ON r.module_id = m.id AND r.module_type = m.type_id JOIN browser_module_gene nm ON m.ensembl=nm.ensembl;

# Prediction
DROP TABLE IF EXISTS `browser_result_prediction`;
CREATE TABLE `browser_result_prediction` (
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  `pcgs_or` double DEFAULT NULL,
  `pcgs_sr` double DEFAULT NULL,
  `pcgspi_or` double DEFAULT NULL,
  `pcgspi_sr` double DEFAULT NULL,
  `pcgspd_or` double DEFAULT NULL,
  `pcgspd_sr` double DEFAULT NULL,
  `pcgspdpird_or` double DEFAULT NULL,
  `pcgspdpird_sr` double DEFAULT NULL,
  `pcgsrd_or` double DEFAULT NULL,
  `pcgsrd_sr` double DEFAULT NULL,
  PRIMARY KEY (`module_id`,`module_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO `browser_result_prediction` SELECT nm.id as module_id, nm.type_id as module_type, r.pcgs_or, r.pcgs_sr, r.pcgspi_or, r.pcgspi_sr, r.pcgspd_or, r.pcgspd_sr, r.pcgspdpird_or, r.pcgspdpird_sr, r.pcgsrd_or, r.pcgsrd_sr FROM browser_010002_06.browser_result_prediction r JOIN browser_010002_06.browser_module_gene m ON r.module_id = m.id AND r.module_type = m.type_id JOIN browser_module_gene nm ON m.ensembl=nm.ensembl;

# Mutations

# CREATE TABLE  `browser_v03_16`.`cosmicSum_08072011` (
#  `ensembl` varchar(128) NOT NULL,
#  `icdo_topography_code` varchar(128) NOT NULL,
#  `icdo_morphology_code` varchar(128) NOT NULL,
#  `found` int(11) NOT NULL,
#  `studied` int(11) NOT NULL
#) ENGINE=MyISAM DEFAULT CHARSET=latin1
# LOAD DATA LOCAL INFILE '/home/jordi/Dropbox/Projectes/BG/intogen_r03/cosmicSum_08072011.data' INTO TABLE `browser_v03_16`.`cosmicSum_08072011`;

DROP TABLE IF EXISTS `browser_result_mutation`;
CREATE TABLE  `browser_result_mutation` (
  `module_id` int(11) NOT NULL,
  `module_type` int(11) NOT NULL,
  `term_id` int(11) NOT NULL,
  `term_type` int(11) NOT NULL,
  `found` int(11) NOT NULL,
  `studied` int(11) NOT NULL,
  PRIMARY KEY (`module_id`,`module_type`,`term_id`,`term_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# Topographies
INSERT INTO browser_result_mutation SELECT m.id as module_id, m.type_id as module_type, t.id as term_id, 4 as term_type, c.found, c.studied FROM intogen_v03.cosmic c JOIN browser_module_gene m ON c.ensembl=m.ensembl JOIN {biomart_db}.ent_icdo t ON t.icdo_topography_code = c.icdo_topography_code AND c.icdo_morphology_code = "NS" AND t.icdo_morphology_code = "";

# Topographies + Morphologies
INSERT INTO browser_result_mutation SELECT m.id as module_id, m.type_id as module_type, t.id as term_id, 5 as term_type, c.found, c.studied FROM intogen_v03.cosmic c JOIN browser_module_gene m ON c.ensembl=m.ensembl JOIN {biomart_db}.ent_icdo t ON t.icdo_topography_code = c.icdo_topography_code AND c.icdo_morphology_code = t.icdo_morphology_code;