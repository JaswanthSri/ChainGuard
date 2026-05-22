# ChainGuard | Serverless Real-Time Cold-Chain Integrity Platform

[cite_start]ChainGuard is a scalable, cloud-native, event-driven serverless backend platform built to solve real-time visibility challenges in cold-chain logistics[cite: 3]. [cite_start]The architecture ingests concurrent telemetry strings from a simulated fleet of 5 IoT transport assets [cite: 3] [cite_start]through AWS IoT Core into an AWS-managed stream processing, storage, and anomaly detection pipeline[cite: 3, 4].

[cite_start]A modern, responsive, high-visibility monitoring dashboard consumes live infrastructure metrics and operational payloads directly via Amazon API Gateway and AWS Lambda REST handlers[cite: 5, 17]. To demonstrate a live, 24/7 production environment, the simulation layer is deployed on an independent cloud micro-server (AWS EC2), ensuring the dashboard reflects dynamic traffic continuously without local dependencies.

---

## Architecture Blueprint

* [cite_start]**Device Simulation Layer:** Multi-threaded Python application simulating 5 concurrent transit delivery trucks broadcasting positional (GPS noise strings) and erratic environmental telemetry over MQTT[cite: 4, 12, 23]. Deployed 24/7 on an AWS EC2 micro-server.
* [cite_start]**Ingestion Layer:** AWS IoT Core Rules Broker routing incoming JSON strings asynchronously into specialized ingestion functions[cite: 4, 13, 24].
* [cite_start]**Persistence Layer:** Amazon DynamoDB dual-table ledger architecture separating structural time-series logs (`Telemetry`) from cached state layers (`Trucks`)[cite: 14].
* [cite_start]**Compute / Processing Engine:** Asynchronous AWS Lambda pipeline executing geospatial Haversine path calculations and threshold drift validation checks to flag real-time structural asset failures (`Alerts`)[cite: 15, 28, 31].
* [cite_start]**API Ingress Layer:** Amazon API Gateway exposing decoupled REST resources securely wrapped with global Cross-Origin Resource Sharing (CORS) configurations[cite: 5, 17].
* [cite_start]**Frontend Hub:** Single-page dashboard built with Tailwind CSS, Lucide icons, and polling-interval async fetch handlers optimized for zero build dependencies and deployed on Vercel[cite: 5, 17].

---

## System Directory Layout

```text
chainguard/
├── backend/
│   └── src/
│       ├── apiHandlerFn/       # REST API Lambda Handler (GET /trucks, GET /alerts)
│       ├── anomalyDetectionFn/ # Geospatial & Temperature Threshold Engine
│       └── ingestTelemetryFn/  # Database Persistence & Orchestration Broker
├── simulation/
│   ├── certs/                  # X.509 Security Certificates (GitIgnored)
│   ├── requirements.txt        # Virtual IoT client device SDKs
│   └── simulator.py            # Multi-threaded 5-Asset Fleet Simulator
└── index.html                  # Main Web Dashboard Interface UI