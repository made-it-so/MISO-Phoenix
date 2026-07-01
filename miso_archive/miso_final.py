import os
import sys
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

# Force the connection parameters manually
os.environ['PYSPARK_SUBMIT_ARGS'] = '--master local[1] pyspark-shell'

builder = SparkSession.builder \
    .appName("MISO_Final") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.ui.enabled", "false")

try:
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    print("\n[MISO-CENTRIC] CONNECTION SUCCESSFUL.")
    
    data = [{"node_id": i, "content": f"Node {i}"} for i in range(2263)]
    df = spark.createDataFrame(data)
    df.write.format("delta").mode("overwrite").save("C:/MISO_RESEARCH/data/bronze/nodes")
    
    print(f"SUCCESS: {df.count()} nodes ingested into Sovereign Bronze Layer.")
    spark.stop()
except Exception as e:
    print(f"\n[ERROR] Handshake Failed: {e}")
