# Scrub

Use the `scrub` utility to sanitize text-files (.csv, .xls, etc) and optionally normalize columns which contain locale specific dates and currencies, if provided with a .metadata file.

Refer to `inspect`'s [README](../inspect/README.md) to learn how to generate a .metadata file.

Running `scrub -f bseg.metadata bseg.csv` on the input file `bseg.csv`:

| mandt | bukrs | belnr      | augdt      |
|-------|-------|------------|------------|
| 100   | 0050  | 0003862080 | 03.16.2020 |
| 100   | 0050  | 0003862081 | 03.16.2020 |
| 100   | 0050  | 0003862082 | 01.23.2020 |
| 100   | 0050  | 0003862091 | 01.30.2020 |

using the following`bseg.metadata` file:

| table_name | column | data_type          |
|------------|--------|--------------------|
| bseg       | mandt  | DECIMAL(38,20)     |
| bseg       | bukrs  | VARCHAR            |
| bseg       | belnr  | VARCHAR            |
| bseg       | augdt  | DATE('02.01.2006') |

Will generate the following tab-separated output file:

|| mandt | bukrs | belnr      | augdt      |
|-------|-------|------------|------------|
| 100   | 0050  | 0003862080 | 2020-03-16 |
| 100   | 0050  | 0003862081 | 2020-03-16 |
| 100   | 0050  | 0003862082 | 2020-01-23 |
| 100   | 0050  | 0003862091 | 2020-01-30 |
 mandt | bukrs | belnr      | augdt      |
|-------|-------|------------|------------|
| 100   | 0050  | 0003862080 | 2020-03-16 |
| 100   | 0050  | 0003862081 | 2020-03-16 |
| 100   | 0050  | 0003862082 | 2020-01-23 |
| 100   | 0050  | 0003862091 | 2020-01-30 |

Here you can see that the `scrub` utility has used the `bseg.metadata` file to correctly convert column `augdt` from date format `month.day.year` to the normalized, [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) `year-month-day` format. 

It's useful to have dates in this format because, when generating an process mining event log, you will often have to create a full timestamp by concatenating two columns like so  `CONCAT(date_column, 'T', time_column, 'Z')`.

## Examples on how to use the options

TODO

# License

GPLv3 License
