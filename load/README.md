# Load

Use the `load` utility to copy the contents of a tab-separated input file into a SQL Database table. `load` uses the provided .metadata file to generate the SQL `CREATE TABLE` that will be executed on the target SQL database.

Refer to `inspect`'s [README](../inspect/README.md) to learn how to generate a .metadata file.

Running `load --environment-file .env bseg.tsv bseg.metadata` performs the following tasks: 

1. Read the value of the `DATABASE_URL` environment variable from the `.env` file to determine which SQL database to connect to
2. Parse the `bseg.metadata` file to generate a SQL `CREATE TABLE` statement which will then be executed on the target SQL database 
3. Copy the contents of the `bseg.tsv` file to the newly created table. 

If you run the `load` command specified above with the contents of the `bseg.tsv` file:

| mandt | bukrs | belnr      | augdt      |
|-------|-------|------------|------------|
| 100   | 0050  | 0003862080 | 2020-03-16 |
| 100   | 0050  | 0003862081 | 2020-03-16 |
| 100   | 0050  | 0003862082 | 2020-01-23 |
| 100   | 0050  | 0003862091 | 2020-01-30 |

whose metadata is specified in the file `bseg.metadata`

| table_name | column | data_type |
|------------|--------|-----------|
| bseg       | mandt  | BIGINT    |
| bseg       | bukrs  | VARCHAR   |
| bseg       | belnr  | VARCHAR   |
| bseg       | augdt  | DATE      |

into the target PostgreSQL "test" database as specified in the `.env` file

``` sh
# Contents of .env file
DATABASE_URL="user:passw0rd@pgsql.local/test"
```

You will be able to execute SQL queries on the `bseg` table like so to retrieve the first row

``` sql
SELECT mandt
FROM bseg
LIMIT 1
```

## Examples on how to use the options

TODO
