# Rapport de reprise de FastFood-BigData

22 novembre 2026

Ce document décrit la première reprise technique. La version rendue pour le jalon 1 complète les exercices RDD, SQL et GraphFrames. Voir le [rapport du jalon 1](Rapport-Jalon-1.pdf) pour les résultats de cette version.

## Audit et corrections

| Composant | Constat et intervention |
| --- | --- |
| Dépôt | La branche locale n'avait aucun commit. Les sources, les données et les captures ont été copiées dans un espace accessible en écriture. Les données et les captures de la copie correspondent à celles de l'original selon SHA-256. |
| Docker et Kafka | Un service initialise les droits du volume Kafka avant le démarrage du broker. Jupyter attend la création idempotente du topic `orders`. Le broker a un contrôle de disponibilité. Le producteur attend l'acquittement de chaque envoi et signale les erreurs de publication. Le mode Kafka conserve le fichier de référence existant. |
| MinIO | Un contrôle HTTP borné précède le démarrage de Jupyter. Le service, Spark et boto3 utilisent les mêmes identifiants configurables. Les ports locaux sont liés à `127.0.0.1`. |
| Spark et RDD | La connexion au cluster reste le comportement par défaut. Les notebooks d'analyse acceptent aussi les fichiers locaux. Le notebook RDD conserve les exercices de partitionnement et compare les résultats au volume réellement chargé. |
| DataFrames et SQL | Les schémas sont centralisés. Le notebook vérifie les statuts, les montants, les horodatages et les références restaurant, puis calcule les KPI sur les commandes livrées dédupliquées et classe les restaurants par ville. |
| GraphFrames | Nouveau notebook sur un graphe orienté restaurants–livreurs avec agrégation des livraisons, validation des degrés entrants et parcours BFS à un saut. Le parcours utilise les expressions SQL attendues par GraphFrames 0.8.3. |

## Résultats

| Contrôle | Résultat |
| --- | --- |
| Validation Compose | `docker compose config --quiet` réussi. |
| Syntaxe Python | Compilation réussie pour les sources et les cellules des cinq notebooks. |
| Données | 50 000 événements, 200 restaurants, 11 127 événements livrés et 10 887 commandes livrées uniques. Toutes les références restaurant correspondent au fichier de référence. |
| Producteur, mode fichier | 100 événements générés dans un répertoire temporaire. |
| Producteur, Kafka simulé | Cinq envois et acquittements vérifiés avec un client simulé. Les fichiers de données n'ont pas changé. |
| Spark RDD local | Toutes les cellules exécutées avec Spark 3.5.9. Les assertions sur les volumes, les partitions, les statuts et les agrégations ont réussi. |
| Spark DataFrames et SQL local | Toutes les cellules exécutées avec Spark 3.5.9, code de sortie 0. Les contrôles de qualité ont réussi et les KPI donnent 2 103 072,95 MAD pour 10 887 commandes livrées uniques. |
| Docker, Kafka, MinIO et exécution distribuée | Docker Desktop est accessible avec les droits élevés. Un cluster isolé a été utilisé en raison d'un conteneur MinIO existant. Les trois services d'initialisation ont terminé avec le code 0, Kafka est sain, les deux workers Spark sont `ALIVE` et Jupyter répond en HTTP 200. Le producteur a publié 10 événements consommés depuis `orders`. Les deux fichiers transférés dans MinIO correspondent aux fichiers locaux par SHA-256. |
| `01_cluster_setup` dans Docker | Exécuté intégralement. Le calcul RDD donne 500 500, le bucket `lake` répond et le client Kafka trouve `orders`. |
| `01b_minio_validation` dans Docker | Exécuté intégralement. Spark a écrit puis relu quatre lignes Parquet sur MinIO via S3A et toutes les assertions ont réussi. Spark a signalé un avertissement de nettoyage de son répertoire temporaire à la fermeture. |
| `02_spark_rdd` dans Docker | Les 16 cellules ont réussi sur les données MinIO, avec 25 000 événements traités par chacun des deux workers dans le test de partitions. |
| `03_spark_dataframes_sql` dans Docker | Les cinq cellules ont réussi sur les données MinIO. La somme des KPI par ville donne 10 887 commandes livrées uniques et 2 103 072,95 MAD de chiffre d’affaires. |
| `04_graphframes` dans Docker | Les trois cellules ont réussi après correction du parcours BFS. Les tests sur les livraisons, les degrés entrants et les chemins à un saut ont réussi. |
| Dossier d'origine | L'écriture dans le dossier OneDrive a été refusée. Les corrections sont dans la copie livrée. |

Le projet cible Spark 3.5.3 dans Docker. Les contrôles locaux utilisent la distribution Spark 3.5.9 disponible sur la machine. Le README indique les commandes de lancement et de validation dans Docker.

À la fermeture de la JVM, Spark a émis un message Windows lié à l’identifiant ou au mot de passe. Les cellules étaient terminées et l’exécution Spark 3.5.9 a renvoyé le code 0.
