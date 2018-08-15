DROP TABLE `flowcache`;

CREATE TABLE `flowcache` (
  `last_time` INT(10) UNSIGNED NOT NULL,
  `abon_id`   INT(11) DEFAULT NULL UNIQUE,
  `octets`    INT(10) UNSIGNED NOT NULL,
  `packets`   INT(10) UNSIGNED NOT NULL,
  KEY `flowcache_abon_id_91e1085d` (`abon_id`)
)
  ENGINE = MEMORY
  DEFAULT CHARSET = utf8;
