-- Django creates a throwaway database named `test_<NAME>` when running the
-- test suite. The application user only receives privileges over the
-- application database, so without this grant `pytest` fails with
-- "1044 Access denied for user 'aveit_dev'@'%' to database 'test_aveit_tribunal_dev'".
-- `\_` escapes the underscore so the pattern matches the literal prefix `test_`.
GRANT ALL PRIVILEGES ON `test\_%`.* TO 'aveit_dev'@'%';
FLUSH PRIVILEGES;
