# Maps

USE `{browser_db}`;

DROP TABLE IF EXISTS `browser_maps`;
CREATE TABLE `browser_maps` (
  `parent_id` int(11) NOT NULL,
  `parent_type` int(11) NOT NULL,
  `child_id` int(11) NOT NULL,
  `child_type` int(11) NOT NULL,
  KEY `parent` (`parent_id`,`parent_type`,`child_type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

# Insert basic maps.

# Expermiments
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 1 as parent_type, m.id as child_id, m.type_id
 FROM browser_source_experiment_platform m;

# Topographies
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 3 as parent_type, m.id as child_id, m.type_id
 FROM browser_term_topography m;

# Genes 
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 6 as parent_type, m.id as child_id, m.type_id
 FROM browser_module_gene m;

# GOs 
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 6 as parent_type, m.id as child_id, m.type_id
 FROM browser_module_go m;

# KEGGs 
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 6 as parent_type, m.id as child_id, m.type_id
 FROM browser_module_kegg m;

# miRNA 
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 6 as parent_type, m.id as child_id, m.type_id
 FROM browser_module_mirna m;

# TFBS 
INSERT INTO `browser_maps`
 SELECT 1 as parent_id, 6 as parent_type, m.id as child_id, m.type_id
 FROM browser_module_tfbs m;

# Topo -> Morpho
INSERT INTO `browser_maps`
 SELECT t.id as parent_id, 4 as parent_type, m.id as child_id, 5 as child_type
 FROM {biomart_db}.ent_icdo m
 JOIN {biomart_db}.ent_icdo t ON m.icdo_topography_code=t.icdo_topography_code AND t.icdo_morphology_code = "" AND m.icdo_morphology_code <> "";

# CREATE TABLE  `go_bp__ensg_v60` (
#   `gene` varchar(128) NOT NULL,
#   `module` varchar(128) NOT NULL
# ) ENGINE=MyISAM DEFAULT CHARSET=latin1
#  SELECT * FROM `intogen_v03`.`go_bp__ensg_v60`

# LOAD DATA LOCAL INFILE '/home/jordi/tmp/modules/go_bp__ensg_v60.tcm' INTO TABLE `intogen_v03`.`go_bp__ensg_v60`;

# GO BP
INSERT INTO `browser_maps`
 SELECT p.id as parent_id, 9 as parent_type, g.id as child_id, 7 as child_type
 FROM `intogen_v03`.`go_bp__ensg_v60` m
 LEFT JOIN browser_module_gene g ON g.ensembl=m.gene
 LEFT JOIN browser_module_go p ON m.module=p.name
 WHERE p.id IS NOT NULL AND g.id IS NOT NULL;

# GO CL
INSERT INTO `browser_maps`
 SELECT p.id as parent_id, 11 as parent_type, g.id as child_id, 7 as child_type
 FROM `intogen_v03`.`go_cl__ensg_v60` m
 LEFT JOIN browser_module_gene g ON g.ensembl=m.gene
 LEFT JOIN browser_module_go p ON m.module=p.name
 WHERE p.id IS NOT NULL AND g.id IS NOT NULL;

# GO MF
INSERT INTO `browser_maps`
 SELECT p.id as parent_id, 10 as parent_type, g.id as child_id, 7 as child_type
 FROM `intogen_v03`.`go_mf__ensg_v60` m
 LEFT JOIN browser_module_gene g ON g.ensembl=m.gene
 LEFT JOIN browser_module_go p ON m.module=p.name
 WHERE p.id IS NOT NULL AND g.id IS NOT NULL;

# Kegg
INSERT INTO `browser_maps`
 SELECT p.id as parent_id, 8 as parent_type, g.id as child_id, 7 as child_type
 FROM `intogen_v03`.`kegg__ensg_v60` m
 LEFT JOIN browser_module_gene g ON g.ensembl=m.gene
 LEFT JOIN browser_module_kegg p ON m.module=p.name
 WHERE p.id IS NOT NULL AND g.id IS NOT NULL;

# miRNA
INSERT INTO `browser_maps`
 SELECT p.id as parent_id, 13 as parent_type, g.id as child_id, 7 as child_type
 FROM `intogen_v03`.`mirna__ensg_v60` m
 LEFT JOIN browser_module_gene g ON g.ensembl=m.gene
 LEFT JOIN browser_module_mirna p ON m.module=p.name COLLATE latin1_general_ci
 WHERE p.id IS NOT NULL AND g.id IS NOT NULL;

# TFBS
INSERT INTO `browser_maps`
 SELECT p.id as parent_id, 12 as parent_type, g.id as child_id, 7 as child_type
 FROM `intogen_v03`.`tfbs__ensg_v60` m
 LEFT JOIN browser_module_gene g ON g.ensembl=m.gene
 LEFT JOIN browser_module_tfbs p ON m.module=p.name
 WHERE p.id IS NOT NULL AND g.id IS NOT NULL;
