from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)

orders_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("restaurant_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("city", StringType(), True),
    StructField("status", StringType(), True),
    StructField("amount_mad", DoubleType(), True),
    StructField("items_count", IntegerType(), True),
    StructField("distance_km", DoubleType(), True),
    StructField("courier_id", StringType(), True),
    StructField("event_time", StringType(), True)
])

restaurants_schema = StructType([
    StructField("restaurant_id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("category", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True)
])
