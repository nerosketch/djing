SELECT
  `base_accounts`.`username`,
  `base_accounts`.`telephone`,
  `abonent`.`ballance`,
  `abonent_tariff`.`tariff_id`,
  `tariffs`.`title`,
  `tariffs`.`speedIn`,
  `tariffs`.`speedOut`,
  `tariffs`.`amount`,
  `groups`.`title`,
  `abon_street`.`name`
FROM `abonent`
  INNER JOIN `base_accounts` ON (`abonent`.`baseaccount_ptr_id` = `base_accounts`.`id`)
  INNER JOIN `groups` ON (`abonent`.`group_id` = `groups`.`id`)
  LEFT OUTER JOIN `abonent_tariff` ON (`abonent`.`current_tariff_id` = `abonent_tariff`.`id`)
  LEFT OUTER JOIN `tariffs` ON (`abonent_tariff`.`tariff_id` = `tariffs`.`id`)
  LEFT OUTER JOIN `abon_street` ON (`abonent`.`street_id` = `abon_street`.`id`)
  LEFT OUTER JOIN `flowcache` ON (`abonent`.`baseaccount_ptr_id` = `flowcache`.`abon_id`)
WHERE (`base_accounts`.`is_admin` = 0 AND `abonent`.`group_id` = 46)
ORDER BY `base_accounts`.`fio` ASC
LIMIT 20;