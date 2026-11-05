# Glue Data Catalog: one database and one explicit external table per gold table.
# No crawler: a crawler would guess types and drift from the models. Column lists come
# from tables.auto.tfvars.json, generated from the exported Parquet schemas.
#
# Arrow -> Glue type mapping is documented in scripts/aws/gen_glue_schema.py.

resource "aws_glue_catalog_database" "gold" {
  # Glue database names allow only lowercase letters, digits and underscores, so the
  # hyphens in name_prefix become underscores here.
  name        = "${replace(var.name_prefix, "-", "_")}_gold"
  description = "GTA Housing gold star schema, published from DuckDB (September vintage). Verification only."
}

resource "aws_glue_catalog_table" "gold" {
  for_each = var.tables

  name          = each.key
  database_name = aws_glue_catalog_database.gold.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.curated.bucket}/gold/${each.key}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    dynamic "columns" {
      for_each = each.value.columns
      content {
        name = columns.value.name
        type = columns.value.type
      }
    }
  }
}
