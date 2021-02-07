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
    usage="%prog [options] target file",
    description="Load a CSV file into a target sql database",
    version="%prog v0.3.0",
    epilog="Load expects to find a .csv.metadata file for the input file "  +
    "describing the schema of the .csv file in SQL DDL format. This file " +
    "can be generated using the `inspect` command in this repo"
)
parser.add_option("-d", "--drop-if-exists", dest="drop", action="store_true",
                  help="Drop existing database schema/tables before creating new")
parser.add_option("-f", "--environment-file", dest="environment_file",
                  help="Location of environment file containing credentials",
                  default=Path('.') / '.env')
parser.add_option("-s", "--db-schema", dest="db_schema", type="string",
                  help="The database schema to load .csv files into")
(options, args) = parser.parse_args()
env = dotenv_values(options.environment_file)

def load_into_sqlite(env, options, target, csv_file):
        path_to_db_file = target[9:]
        (table_name, _) = splitext(basename(csv_file))
        sanitized_table_name = re.sub(r"-|\s", '_', table_name)
        if options.drop:
            os.remove(path_to_db_file)
        con = sqlite3.connect(path_to_db_file)
        cur = con.cursor()
        create_stmt = create_stmt_ddl_from(f"{csv_file}.metadata") 
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

def load_into_postgresql(env, options, csv_file):
    create_stmt = create_stmt_ddl_from(f"{csv_file}.metadata")
    db_uri = f'postgres://{env["PSQL_USERNAME"]}:{env["PSQL_PASSWORD"]}' +\
    f'@{env["PSQL_HOST"]}/{env["PSQL_DB"]}'
    (table_name, _) = splitext(basename(csv_file))
    engine = create_engine(db_uri)
    conn = engine.connect()
    if options.drop:
        drop_schema_then_create = text(f'\
        DROP SCHEMA IF EXISTS "{options.db_schema}" CASCADE;\
        CREATE SCHEMA "{options.db_schema}";')
        conn.execute(drop_schema_then_create)
    if options.db_schema:
        conn.execute(f'SET search_path TO "{options.db_schema}";')
    create_stmt = f'CREATE TABLE IF NOT EXISTS {table_name} ( ' + create_stmt + ";"
    conn.execute(create_stmt)
    psql_copy(db_uri, options.db_schema, csv_file)

def create_stmt_ddl_from(csv_metadata_file):
    create_stmt = ""
    with open(csv_metadata_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter="|")
        first_row = next(reader)
        if first_row["data_type"].startswith("DECIMAL"):
            create_stmt = f'{first_row["column_name"]} {first_row["data_type"]},'   
        else:
            create_stmt = f'{first_row["column_name"]} {re.findall("[^(]+", first_row["data_type"])[0]},'
        for row in reader:
            if row["data_type"].startswith("DECIMAL"):
                create_stmt += f' {row["column_name"]} {row["data_type"]},'
            else:
                create_stmt += f' {row["column_name"]} {re.findall("[^(]+", row["data_type"])[0]},'
        create_stmt = create_stmt[:-1] + ')'
    return create_stmt
    
def psql_copy(db_uri, db_schema, csv_file):
   
   (table_name, _) = splitext(basename(csv_file))
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

def as_parquet(csv_file):
    
    result = io.BytesIO()
    csv_parse_options = csv.ParseOptions(delimiter="\t")
    schema_parse_options = csv.ParseOptions(delimiter="|")
    schema = csv.read_csv(
        f"{csv_file}.metadata",
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

def load_into_athena(env, path_to_csv_file):

    aws_session = boto3.Session(
        region_name = env["AWS_REGION_NAME"],
        aws_access_key_id = env["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key = env["AWS_SECRET_ACCESS_KEY"]
    )
    (table_name, _) = splitext(basename(path_to_csv_file))
    parquet = as_parquet(path_to_csv_file)
    s3 = aws_session.resource('s3')
    print(f'Copy from {path_to_csv_file}.parquet to s3://{env["BUCKET_NAME"]}/{table_name}/{basename(path_to_csv_file)}.parquet')
    s3.Object(
        env['BUCKET_NAME'],
        f"{table_name}/{basename(path_to_csv_file)}.parquet"
    ).put(Body=parquet.getvalue())
    create_stmt = create_stmt_ddl_from(f"{path_to_csv_file}.metadata")
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
    target = args.pop(0)
    csv_file = args.pop(0)
    if target.startswith("postgresql"):
        load_into_postgresql(env, options, target, csv_file)
    elif target.startswith("athena"):
        load_into_athena(env, options, target, csv_file)
    elif target.startswith("sqlite"):
        load_into_sqlite(env, options, target, csv_file)
    else:
        print(f"The database of type `{options.db_target.split('/')[:-1]}` is not supported")

if __name__ == "__main__":
    run()
