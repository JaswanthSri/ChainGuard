# ChainGuard | Serverless Real-Time Cold-Chain Integrity Platform

ChainGuard is a scalable, cloud-native, event-driven serverless backend platform built to solve
real-time visibility challenges in cold-chain logistics. The architecture ingests concurrent
telemetry strings from a simulated fleet of 5 IoT transport assets through AWS IoT Core into an
AWS-managed stream processing, storage, and anomaly detection pipeline.

A modern, responsive, high-visibility monitoring dashboard consumes live infrastructure metrics
and operational payloads directly via Amazon API Gateway and AWS Lambda REST handlers. To
demonstrate a live, 24/7 production environment, the simulation layer runs on an independent
cloud micro-server (AWS EC2), ensuring the dashboard reflects dynamic traffic continuously
without local dependencies.

---

## AWS Cloud Stack & Technology Breakdown

This project utilizes a fully integrated suite of AWS services, operating within the AWS Free
Tier limitations:

**AWS EC2 (Elastic Compute Cloud)**
Hosts the multi-threaded Python simulation script 24/7 inside an Ubuntu `t2.micro` instance
using background execution (`nohup`), serving as our persistent edge-device simulator fleet.

**AWS IoT Core**
Acts as the managed MQTT broker that handles secure device connectivity. It utilizes X.509
certificates for truck authentication and applies an IoT SQL Rule to forward telemetry payloads
to the ingestion tier.

**AWS Lambda**
Powers the entire serverless, zero-maintenance compute layer through three dedicated functions:

- `ingestTelemetryFn` — Parses, validates, and records incoming payloads to the database.
- `anomalyDetectionFn` — Computes geospatial Haversine path checks and tracks rolling thermal
  limits asynchronously.
- `apiHandlerFn` — Fetches database states and feeds cleanly structured data to the web client.

**Amazon DynamoDB**
A fully managed, NoSQL, on-demand database optimized for high-speed write loops. Utilizes
separate tables for time-series historic archives (`Telemetry`), a real-time vehicle state
cache (`Trucks`), active incidents (`Alerts`), and expected geofences (`Routes`).

**Amazon API Gateway**
Exposes the backend Lambda functions as public, secure REST API endpoints (`GET /trucks` and
`GET /alerts`) configured with full Cross-Origin Resource Sharing (CORS) policies to integrate
with external clients.

**Vercel (Frontend Hosting)**
Hosts the static `index.html` file, providing global delivery, continuous GitHub deployment,
and 4-second polling intervals to mirror live cloud telemetry.

---

## System Directory Layout

```text
chainguard/
│
├── backend/
│   └── src/
│       ├── apiHandlerFn/         # REST API Lambda Handler (GET /trucks, GET /alerts)
│       ├── anomalyDetectionFn/   # Geospatial & Temperature Threshold Engine
│       └── ingestTelemetryFn/    # Database Persistence & Orchestration Broker
│
├── simulation/
│   ├── certs/                    # X.509 Security Certificates (GitIgnored)
│   ├── requirements.txt          # Virtual IoT client device SDKs
│   └── simulator.py              # Multi-threaded 5-Asset Fleet Simulator
│
└── index.html                    # Main Web Dashboard Interface UI
```