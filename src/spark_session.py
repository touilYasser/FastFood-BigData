import os

from pyspark.sql import SparkSession


def create_spark_session(
    app_name="FastFood-BigData",
    enable_graphframes=False,
    enable_streaming=False,
    enable_delta=False,
    enable_s3=True
):

    packages = []
    if enable_s3:
        packages.append("org.apache.hadoop:hadoop-aws:3.3.4")

    if enable_graphframes:
        packages.append(
            "graphframes:graphframes:0.8.3-spark3.5-s_2.12"
        )

    if enable_streaming:
        packages.append(
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3"
        )

    if enable_delta:
        packages.append(
            "io.delta:delta-spark_2.12:3.2.1"
        )

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(os.getenv("FASTFOOD_SPARK_MASTER", "spark://spark-master:7077"))
        .config("spark.executor.memory", "1g")
        .config("spark.executor.cores", "2")
        .config("spark.cores.max", "4")

        .config(
            "spark.hadoop.fs.s3a.endpoint",
            os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            os.getenv("MINIO_ROOT_USER", "minioadmin")
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
        )
        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            "true"
        )
        .config(
            "spark.hadoop.fs.s3a.connection.ssl.enabled",
            "false"
        )
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem"
        )
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
        )

        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.session.timeZone", "UTC")
    )

    if packages:
        builder.config("spark.jars.packages", ",".join(packages))
    if enable_graphframes:
        builder.config("spark.jars.repositories", "https://repos.spark-packages.org/")

    if not os.getenv("FASTFOOD_SPARK_MASTER", "").startswith("local"):
        builder.config("spark.driver.host", "jupyter")
        builder.config("spark.driver.bindAddress", "0.0.0.0")

    if enable_delta:
        builder = (
            builder
            .config(
                "spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension"
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog"
            )
        )

    spark = builder.getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    return spark