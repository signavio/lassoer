#!/usr/bin/env python3
from botocore.config import Config
from dotenv import dotenv_values
from optparse import OptionParser
from os.path import basename, splitext
from pathlib import Path
from pyarrow import csv
from pyarrow import parquet
from shlex import quote
from sqlalchemy import create_engine, text
from subprocess import Popen, PIPE
import boto3, csv, re, os, json, io, sys, sqlite3
import pyarrow as pa

parser = OptionParser(
    usage="%prog [options] file metadata",
    description="Load a CSV file into a target sql database",
    version="%prog v0.3.0",
    epilog="Use the `load` utility to copy the contents of a tab-separated" +
        " input file into a SQL Database table. `load` uses the metadata" +
        " argument to generate the SQL `CREATE TABLE` that will be" +
        " executed on the target SQL database"
)
parser.add_option("-d", "--drop-if-exists", dest="drop", action="store_true",
                  help="Drop existing database table before creating new")
parser.add_option("-f", "--environment-file", dest="environment_file",
                  help="Location of environment file containing credentials",
                  default=Path('.') / '.env')
parser.add_option("-s", "--db-schema", dest="db_schema", type="string",
                  help="The database schema to load .csv files into")
(options, args) = parser.parse_args()
env = dotenv_values(options.environment_file)

def load_into_sqlite(env, options, target, csv_file, metadata_file):
        path_to_db_file = target[9:]
        table_name = basename(csv_file).split('.')[0]
        sanitized_table_name = re.sub(r"-|\s", '_', table_name)
        if options.drop:
            cur.execute(f'DROP TABLE IF EXISTS "{sanitized_table_name}"')
        con = sqlite3.connect(path_to_db_file)
        cur = con.cursor()
        create_stmt = create_stmt_ddl_from(metadata_file) 
        cur.execute(f'CREATE TABLE IF NOT EXISTS "{sanitized_table_name}" ({create_stmt};')
        # Do not use the con with csv.DictReader to load data from csv_file
        # into the db, since .import with sqlite3 works well enough
        con.close()
        import_text = ".headers on\n" +\
        ".mode csv\n" +\
        ".separator '\t'\n" +\
        f'.import \'{csv_file}\' "{sanitized_table_name}"'
        process = Popen(f"sqlite3 {path_to_db_file}", stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)
        stdout, stderr = process.communicate(bytes(import_text, encoding="UTF-8"))
        if len(stdout) > 0:
            rows_copied = stdout.decode("utf-8")[:-1] 
            print(rows_copied)
        if len(stderr) > 0:
            print(stderr.decode("utf-8")[:-1])

def load_into_postgresql(env, options, target, csv_file, metadata_file):
    create_stmt = create_stmt_ddl_from(metadata_file)
    db_uri = target
    table_name = basename(csv_file).split('.')[0]
    engine = create_engine(db_uri)
    conn = engine.connect()
    if options.drop:
        conn.execute(f'DROP TABLE IF EXISTS "{options.db_schema}".{table_name};')
    conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{options.db_schema}";')
    create_stmt = f'CREATE TABLE IF NOT EXISTS "{options.db_schema}".{table_name} ( ' + create_stmt + ";"
    conn.execute(create_stmt)
    psql_copy(db_uri, options.db_schema, csv_file)

def create_stmt_ddl_from(metadata_file):
    create_stmt = ""
    with open(metadata_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter="|")
        first_row = next(reader)
        if first_row["data_type"].startswith("DECIMAL"):
            create_stmt = f'"{first_row["column_name"].lower()}" {first_row["data_type"]},'
        else:
            create_stmt = f'"{first_row["column_name"].lower()}" {re.findall("[^(]+", first_row["data_type"])[0]},'
        for row in reader:
            if row["data_type"].startswith("DECIMAL"):
                create_stmt += f' "{row["column_name"].lower()}" {row["data_type"]},'
            else:
                create_stmt += f' "{row["column_name"].lower()}" {re.findall("[^(]+", row["data_type"])[0]},'
        create_stmt = create_stmt[:-1] + ')'
    return create_stmt
    
def psql_copy(db_uri, db_schema, csv_file):
    table_name = basename(csv_file).split('.')[0]
    psql_copy_cmd = [
    'psql', db_uri,
    '-c', f'\COPY "{db_schema}".{table_name} ' +\
    f'FROM {csv_file} WITH ' +\
    "DELIMITER AS '\t' " +\
    "NULL AS '' " +\
    "CSV HEADER " +\
    "QUOTE AS '\"' " +\
    "ESCAPE AS '\"'"
    ]
    process = Popen(psql_copy_cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if len(stdout) > 0:
       rows_copied = stdout.decode("utf-8")[:-1] 
       print(f'{rows_copied} rows from {csv_file} to "{db_schema}".{table_name}')
    if len(stderr) > 0:
       print(stderr.decode("utf-8")[:-1])

def create_pyarrow_schema(column_names, data_types):
    fields = []
    names_types = zip(column_names, data_types)
    for (n, t) in names_types:
        if str(t).startswith("DECIMAL"):
            fields.append((str(n), pa.float64()))
        elif str(t).startswith("NUMERIC"):
            fields.append((str(n), pa.decimal128(38, 20)))
        elif str(t).startswith("VARCHAR"):
            fields.append((str(n), pa.string()))
        elif str(t).startswith("TIMESTAMP"):
            fields.append((str(n), pa.timestamp('us',tz="UTC")))
        elif str(t).startswith("TIME"):
            # Since CSV conversion to time64 is not supported
            fields.append((str(n), pa.string()))
        elif str(t).startswith("DATE"):
            fields.append((str(n), pa.date64()))
        elif str(t).startswith("INTEGER"):
            fields.append((str(n), pa.int64()))
        elif str(t).startswith("FLOAT"):
            fields.append((str(n), pa.float64()))
        elif str(t).startswith("DOUBLE"):
            fields.append((str(n), pa.float64()))
        elif str(t).startswith("BOOLEAN"):
            fields.append((str(n), pa.bool_()))
        else:
            fields.append((str(n), pa.string()))
    return pa.schema(fields)

def as_parquet(csv_file, metadata_file):
    
    result = io.BytesIO()
    csv_parse_options = csv.ParseOptions(delimiter="\t")
    schema_parse_options = csv.ParseOptions(delimiter="|")
    schema = csv.read_csv(
        metadata_file,
        parse_options=schema_parse_options
    )
    pyarrow_schema = create_pyarrow_schema(schema["column_name"], schema["data_type"])
    csv_convert_options = csv.ConvertOptions(column_types=pyarrow_schema)
    parquet_table = csv.read_csv(
            csv_file,
            parse_options=csv_parse_options,
            convert_options=csv_convert_options
    )
    w = parquet.ParquetWriter(
        where=result,
        schema=pyarrow_schema,
        compression="SNAPPY",
        flavor="spark"
    )
    w.write_table(parquet_table) 
    return result

def load_into_athena(env, csv_file, metadata_file):

    aws_session = boto3.Session(
        region_name = env["AWS_REGION_NAME"],
        aws_access_key_id = env["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key = env["AWS_SECRET_ACCESS_KEY"]
    )

    table_name = basename(csv_file).split('.')[0]
    parquet = as_parquet(csv_file)
    s3 = aws_session.resource('s3')
    print(f'Copy from {csv_file}.parquet to s3://{env["BUCKET_NAME"]}/{table_name}/{basename(csv_file)}.parquet')
    s3.Object(
        env['BUCKET_NAME'],
        f"{table_name}/{basename(csv_file)}.parquet"
    ).put(Body=parquet.getvalue())
    create_stmt = create_stmt_ddl_from(metadata_file)
    client = aws_session.client('athena')
    create_stmt = re.sub("VARCHAR|TIME", "string", create_stmt) 
    query = f"CREATE EXTERNAL TABLE IF NOT EXISTS {table_name} (" +\
            create_stmt + " " +\
            "STORED AS PARQUET " +\
            f"LOCATION 's3://{env['BUCKET_NAME']}/{table_name}/' " +\
            'TBLPROPERTIES ("parquet.compression"="SNAPPY");'
    print(query)
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': env['ATHENA_NAME']
        },
        ResultConfiguration={
            'OutputLocation': f's3://{env["BUCKET_NAME"]}/__logs/',
            'EncryptionConfiguration': {
                'EncryptionOption': 'SSE_S3'
            }
        },
        WorkGroup=env['ATHENA_WORKGROUP']
    )
    print(f'"{env["ATHENA_NAME"]}"."{table_name}" created and populated successfully')
    print(json.dumps(response,indent=2))

def run():
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)
    csv_file = args.pop(0)
    metadata_file = args.pop(0)
    try:
        target = env["DATABASE_URL"]
    except KeyError:
        print("The environment file must specify a valid $DATABASE_URL variable")
        sys.exit(1)
    if target.startswith("postgresql"):
        if options.db_schema is None:
            print("A Database schema must be provided using option -d")
            sys.exit(1)
        load_into_postgresql(env, options, target, csv_file, metadata_file)
    elif target.startswith("athena"):
        load_into_athena(env, csv_file, metadata_file)
    elif target.startswith("sqlite"):
        load_into_sqlite(env, options, target, csv_file, metadata_file)
    else:
        print(f"The database of type `{target.split('/')[:-1]}` is not supported")

if __name__ == "__main__":
    run()
