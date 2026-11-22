import os

from pathlib import Path
import boto3

# Racine du projet
ROOT = Path(__file__).resolve().parents[1]

# Configuration MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
    aws_access_key_id=os.getenv("MINIO_ROOT_USER", "minioadmin"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
    region_name="us-east-1"
)

BUCKET = "lake"

FILES = {
    "orders_history.jsonl": "bronze/history/orders_history.jsonl",
    "restaurants.json": "bronze/reference/restaurants.json"
}


def main():
    # Vérifier que les fichiers sources existent
    for filename in FILES:
        path = ROOT / "data" / filename

        if not path.is_file():
            raise FileNotFoundError(
                f"Fichier introuvable : {path}. "
                "Exécute d'abord producer.py."
            )

    # Créer le bucket si nécessaire
    buckets = [
        bucket["Name"]
        for bucket in s3.list_buckets()["Buckets"]
    ]

    if BUCKET not in buckets:
        s3.create_bucket(Bucket=BUCKET)
        print(f"Bucket créé : {BUCKET}")

    # Charger les fichiers dans MinIO
    for filename, key in FILES.items():
        path = ROOT / "data" / filename

        s3.upload_file(
            Filename=str(path),
            Bucket=BUCKET,
            Key=key
        )

        metadata = s3.head_object(
            Bucket=BUCKET,
            Key=key
        )

        print(
            f"UPLOAD OK : s3://{BUCKET}/{key} "
            f"({metadata['ContentLength']} octets)"
        )

    print("\nUPLOAD COMPLETED")


if __name__ == "__main__":
    main()
