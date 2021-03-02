# Inspect

Use the `inspect` utility to guess at the metadata of a .csv file and try to determine column data types (strings, dates, numbers, etc.) 

Running `inspect -d '02.01.2006' bseg.csv` using the following `bseg.csv` file:

| mandt | bukrs | belnr      | augdt      |
|-------|-------|------------|------------|
| 100   | 0050  | 0003862080 | 03.16.2020 |
| 100   | 0050  | 0003862081 | 03.16.2020 |
| 100   | 0050  | 0003862082 | 01.23.2020 |
| 100   | 0050  | 0003862091 | 01.30.2020 |

will generate the following .metadata output file:

| table_name | column | data_type          |
|------------|--------|--------------------|
| bseg       | mandt  | DECIMAL(38,20)     |
| bseg       | bukrs  | VARCHAR            |
| bseg       | belnr  | VARCHAR            |
| bseg       | augdt  | DATE('02.01.2006') |

The `data_type` column uses a syntax similar to what you would use in a SQL `CREATE TABLE` statement with the added advantage that you can specify locale specific date and time formatting per column. 

## Date, time and currency formatting

The data types `TIMESTAMP()`, `TIME()`, `DATE()` and `NUMERIC()` accept an optional formatting parameter (delineated using single or double quotes) which can be used to correctly identify columns formatted in various locales.

Instead of specifying a formatting string using arcane `%Y` or `%m` characters, as is the case in the [POSIX `strptime` standard](https://man7.org/linux/man-pages/man3/strptime.3p.html), `inspect` uses the approach pioneered by [golang's `time` package](https://golang.org/pkg/time/#pkg-constants).

As shown in the example above, you specify what **the reference time** looks like in the column's _target_ format. **The reference time** correlates to a specific point in time, namely to Monday, January 2 15:04:05 2006 (Mountain Standard Time), which is equivalent to the unix epoch time `1136239445`. The reference time is easy to remember because it can also be thought of as `01/02 03:04:05PM '06 -0700`.

Some columns may also contain currencies (or other rational numbers) that are formatted with locale specific decimal and/or grouping marks. This could be the case for instance when we have a column called `CHF` representing Swiss Francs as `203'999.99` for example. You can use the `inspect` command with option `-n` to specify what the **the reference currency** looks like formatted as Swiss Francs.

**The reference currency** correlates to the value "eight thousand nine hundred and ninety nine euros and ninety nine cents". Calling `inspect -n "8'999.99"` on the input file containing column `CHF` would generate the following .metadata output file:

| table_name | column | data_type           |
|------------|--------|---------------------|
| bseg       | CHF    | NUMERIC('8'999.99') |

Which allows us to specify that column `CHF` is of data type `NUMERIC` whose format consists of a single quote `'` as grouping mark and a dot `.` as decimal mark.

## Examples on how to use the options

TODO

# License

GPLv3 License
