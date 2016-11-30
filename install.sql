CREATE TABLE flowstat (
  `id`       INT(10) AUTO_INCREMENT NOT NULL,
  `src_ip`   CHAR(8)                NOT NULL,
  `dst_ip`   CHAR(8)                NOT NULL,
  `proto`    SMALLINT(2) UNSIGNED   NOT NULL DEFAULT 0,
  `src_port` SMALLINT(5) UNSIGNED   NOT NULL DEFAULT 0,
  `dst_port` SMALLINT(5) UNSIGNED   NOT NULL DEFAULT 0,
  `octets`   INT UNSIGNED           NOT NULL DEFAULT 0,
  `packets`  INT UNSIGNED           NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
)
  ENGINE =MyISAM
  DEFAULT CHARSET =utf8;


INSERT INTO flowstat (`src_ip`, `dst_ip`, `proto`, `src_port`, `dst_port`, `octets`, `packets`) VALUES
  ('c0a80201', 'c0a805ba', 6, 49150, 443, 5281, 13),
  ('c0a80201', 'c0a805ba', 6, 49150, 443, 5281, 13)
