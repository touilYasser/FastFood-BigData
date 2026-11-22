# FastFood-BigData

Pipeline de démonstration pour analyser des événements de commande. Kafka transporte les événements simulés, MinIO stocke les fichiers historiques et Spark exécute les analyses distribuées.

## Jalon 1

Le [rapport PDF](docs/Rapport-Jalon-1.pdf) couvre le déploiement, les RDD, Spark SQL et le graphe clients–restaurants. Les [captures de validation](docs/screenshots/jalon1/) montrent notamment les deux workers, les DAG, le plan SQL, le contenu MinIO et les résultats GraphFrames.

## Lancement avec Docker Desktop

Depuis la racine du projet, avec le moteur Docker Linux démarré :

```powershell
docker compose config --quiet
docker compose build spark-master
docker compose up -d
docker compose ps -a
docker compose exec jupyter python3 /opt/project/producer/producer.py --mode file --n 50000
docker compose exec jupyter python3 -m src.upload_data
```

Le build explicite crée l’image partagée avant que les workers et les services d’initialisation en aient besoin. `kafka-volume-init` règle les droits du volume avant le démarrage de Kafka. Kafka doit être joignable avant la création du topic `orders`. Jupyter attend la création du topic et la réponse HTTP de MinIO. Les conteneurs `kafka-volume-init`, `kafka-init` et `minio-ready` doivent sortir avec le code 0.

Depuis un clone Git, la commande `--mode file` génère l’historique de 50 000 événements. Elle réécrit aussi le fichier des restaurants. Si les deux fichiers sont déjà présents et doivent être conservés, passer directement au chargement MinIO.

Ouvrir [Jupyter](http://localhost:8888/?token=fastfood) et exécuter les notebooks dans l’ordre. Le jeton par défaut peut être changé dans `.env`, à partir de `.env.example`. Les ports publiés sont liés à l’interface de boucle locale.

| Notebook | Vérifications |
| --- | --- |
| `01_cluster_setup` | Calcul Spark, répartition des tâches, topic Kafka et accès au bucket |
| `01b_minio_validation` | Écriture et lecture Parquet avec Spark S3A |
| `02_spark_rdd` | Chiffre d’affaires, panier moyen, statuts, doublons et partitions |
| `03_spark_dataframes_sql` | KPI DataFrame et SQL, jointure, UDF et expression native, plan Catalyst et écriture Parquet partitionnée dans Silver |
| `04_graphframes` | Graphe clients–restaurants depuis Silver, degrés, PageRank, composantes connexes, motifs et CA avec `aggregateMessages` |

Exécuter la partie 3 avant la partie 4 pour créer `s3a://lake/silver/orders_history/`. Pour suivre les parties 2 et 3, ouvrir [Spark UI](http://localhost:4040) pendant l’exécution. Dans l’onglet Jobs, cliquer sur un job, puis sur DAG Visualization. L’onglet Stages affiche les tâches et les volumes de shuffle. Pour garder l’interface ouverte deux minutes en fin de calcul, mettre `FASTFOOD_UI_HOLD_SECONDS=120` dans `.env` avant `docker compose up -d`. Dans Jupyter, on peut aussi avancer cellule par cellule et observer l’interface avant l’appel à `spark.stop()`.

### Vérifier les services et les données

- [Spark Master](http://localhost:8080) affiche deux workers `ALIVE`.
- [MinIO](http://localhost:9001) utilise par défaut le compte `minioadmin` et le mot de passe `minioadmin123`. Dans `lake`, ouvrir `bronze/history/` après le chargement, puis `silver/orders_history/` après la partie 3. Silver comporte quatre répertoires `city=…`.
- Pour vérifier les trois partitions de Kafka, lancer `docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --describe --topic orders`.

Si des ports sont déjà occupés, personnaliser les ports hôte dans `.env`. Par exemple, `MINIO_API_PORT=19000` et `MINIO_CONSOLE_PORT=19001` déplacent MinIO vers les ports 19000 et 19001. Pour un second cluster complet, utiliser un autre nom de projet (`docker compose -p fastfood-demo …`) et des ports hôte distincts pour chaque service. Les connexions entre conteneurs restent sur les ports d’origine.

Démarrer chaque notebook avec un noyau neuf. Les JAR Hadoop AWS et GraphFrames sont résolus au premier lancement qui en a besoin. Le cache Ivy est conservé dans un volume. En cas de blocage au démarrage de Spark, identifier le dépôt ou l’artefact indiqué dans les logs Ivy avant de relancer. GraphFrames 0.8.3 est configuré pour Spark 3.5 et Scala 2.12.

Pour publier un échantillon sur Kafka et vérifier son arrivée :

```powershell
docker compose exec jupyter python3 /opt/project/producer/producer.py --mode kafka --n 10 --rate 5
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:29092 --topic orders --from-beginning --max-messages 10 --timeout-ms 10000
```

Les messages du producteur sont acquittés par Kafka. Sur un topic déjà utilisé, la commande de lecture affiche les premiers messages conservés. Pour diagnostiquer le démarrage, utiliser `docker compose logs kafka kafka-init minio minio-ready spark-master spark-worker-1 spark-worker-2 jupyter`.

## Contrôles Spark locaux

Depuis la racine, avec PySpark 3.5 et Java disponibles :

```powershell
python run_local_checks.py 02_spark_rdd 03_spark_dataframes_sql
```

Le script exécute les cellules sur les fichiers existants avec deux threads locaux. Les résultats des mesures RDD dépendent du cache, de l’ordre des exécutions et de l’environnement.
