SELECT t0.*,
       sum(t0.`two`) OVER (PARTITION BY t0.`three` ORDER BY t0.`one` ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS `four`
FROM my_data t0