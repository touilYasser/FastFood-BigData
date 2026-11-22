
import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CITIES = {
    "Casablanca": ("CAS", 33.5731, -7.5898),
    "Rabat": ("RAB", 34.0209, -6.8416),
    "Marrakech": ("MAR", 31.6295, -7.9811),
    "Tanger": ("TAN", 35.7595, -5.8340),
}

CATEGORIES = ["pizza", "tacos", "sushi", "marocain", "burger"]


def generate_restaurants(rng, write_file=True):
    restaurants = []

    for number in range(1, 201):
        city = list(CITIES)[(number - 1) % 4]
        _, latitude, longitude = CITIES[city]

        restaurants.append({
            "restaurant_id": f"R-{number:03d}",
            "name": f"Restaurant {number:03d}",
            "city": city,
            "category": rng.choice(CATEGORIES),
            "latitude": round(latitude + rng.uniform(-0.04, 0.04), 6),
            "longitude": round(longitude + rng.uniform(-0.04, 0.04), 6),
        })

    if write_file:
        path = DATA_DIR / "restaurants.json"

        with path.open("w", encoding="utf-8") as file:
            for restaurant in restaurants:
                file.write(json.dumps(restaurant, ensure_ascii=False) + "\n")

        print(f"Generated {len(restaurants)} restaurants: {path}")
    return restaurants


def generate_events(n, mode, rate):
    rng = random.Random(42)
    restaurants = generate_restaurants(rng, write_file=(mode == "file"))

    start = datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc)
    pending = {}
    history = []
    next_order_number = 1

    producer = None

    if mode == "kafka":
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
            acks="all",
            key_serializer=lambda value: value.encode("utf-8"),
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    output = DATA_DIR / "orders_history.jsonl"
    file = output.open("w", encoding="utf-8") if mode == "file" else None

    try:
        for index in range(n):
            # Approximately 2% repeated events.
            if history and rng.random() < 0.02:
                event = dict(rng.choice(history))

            else:
                create_new = not pending or rng.random() < 0.45

                if create_new:
                    restaurant = rng.choice(restaurants)
                    city = restaurant["city"]
                    code = CITIES[city][0]

                    order_id = f"ORD-{next_order_number:07d}"
                    next_order_number += 1

                    event = {
                        "order_id": order_id,
                        "restaurant_id": restaurant["restaurant_id"],
                        "customer_id": f"C-{rng.randint(1, 10000):05d}",
                        "city": city,
                        "status": "CREATED",
                        "amount_mad": round(rng.uniform(35, 350), 2),
                        "items_count": rng.randint(1, 8),
                        "distance_km": round(rng.uniform(0.5, 12), 2),
                        "courier_id": f"L-{code}-{rng.randint(1, 99):02d}",
                        "event_time": None,
                    }

                    pending[order_id] = event

                else:
                    order_id = rng.choice(list(pending))
                    previous = pending[order_id]

                    event = dict(previous)

                    if previous["status"] == "CREATED":
                        event["status"] = (
                            "CANCELLED"
                            if rng.random() < 0.08
                            else "PICKED_UP"
                        )
                    else:
                        event["status"] = "DELIVERED"

                    if event["status"] in ("DELIVERED", "CANCELLED"):
                        del pending[order_id]
                    else:
                        pending[order_id] = event

                if mode == "file":
                    timestamp = start + timedelta(seconds=index * 5)
                else:
                    timestamp = datetime.now(timezone.utc)

                # Simulate approximately 5% late event timestamps.
                if rng.random() < 0.05:
                    timestamp -= timedelta(minutes=rng.randint(1, 15))

                event["event_time"] = timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                if event["status"] == "CREATED":
                    pending[order_id] = event

                history.append(dict(event))

            if file:
                file.write(json.dumps(event, ensure_ascii=False) + "\n")
            else:
                producer.send(
                    "orders",
                    key=event["order_id"],
                    value=event,
                ).get(timeout=30)

                time.sleep(1 / rate)

            if (index + 1) % 10000 == 0:
                print(f"Generated {index + 1}/{n} events")

        if producer:
            producer.flush()

    finally:
        if file:
            file.close()

        if producer:
            producer.close()

    print(f"Generation completed: {n} events")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["file", "kafka"],
        required=True,
    )
    parser.add_argument("--n", type=int, default=50000)
    parser.add_argument("--rate", type=float, default=20)

    args = parser.parse_args()

    if args.n < 1 or args.rate <= 0:
        parser.error("--n and --rate must be positive")

    generate_events(args.n, args.mode, args.rate)
