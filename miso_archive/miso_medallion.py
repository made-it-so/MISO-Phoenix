import os
import sys
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

# 1. Force Windows Handshake Axioms
os.environ['PYSPARK_SUBMIT_ARGS'] = '--master local[2] pyspark-shell'
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# 2. Initialize Sovereign Engine
builder = SparkSession.builder \
    .appName("MISO_Local_Medallion") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.warehouse.dir", "C:/MISO_RESEARCH/warehouse") \
    .config("spark.driver.extraJavaOptions", "-Dderby.system.home=C:/MISO_RESEARCH/derby")

spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("\n[MISO-CENTRIC] Substrate Active. Processing 2,263 Nodes...")

# 3. Create/Ingest Data
data = [{"node_id": i, "content": f"Axiom {i}", "category": "Compliance"} for i in range(2263)]
df = spark.createDataFrame(data)

# 4. Execute Medallion Layers
print("-> Writing BRONZE (Raw Ingestion)...")
df.write.format("delta").mode("overwrite").save("C:/MISO_RESEARCH/data/bronze/nodes")

print("-> Refining SILVER (Cleansed Axioms)...")
silver_df = spark.read.format("delta").load("C:/MISO_RESEARCH/data/bronze/nodes")
silver_df.write.format("delta").mode("overwrite").save("C:/MISO_RESEARCH/data/silver/nodes")

print("-> Finalizing GOLD (Sovereign Intelligence)...")
gold_df = silver_df.groupBy("category").count()
gold_df.show()
gold_df.write.format("delta").mode("overwrite").save("C:/MISO_RESEARCH/data/gold/node_summary")

print("\n[SUCCESS] Local Medallion Substrate Created.")
spark.stop()
