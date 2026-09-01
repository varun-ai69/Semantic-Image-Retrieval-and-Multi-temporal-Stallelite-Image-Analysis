# Data & Model Provenance Log (`PROVENANCE.md`)

## Overview & Purpose

This document serves as the official **Data and Model Lineage Audit Log** for the *Semantic Retrieval & Multi-Temporal Change Analysis of Satellite Imagery* project (PS SIH-26227 for Indian Army DGIS / Ministry of Defence).

To ensure complete transparency, security compliance, and licensing auditability in a **fully on-premises and air-gapped environment**, every dataset, pre-trained model checkpoint, and open-source dependency ingested into the platform must be logged in this document prior to deployment.

---

## 📋 Tracked Metadata Fields

For every ingested component, the following metadata fields are tracked:

1. **Item Name**: Descriptive identifier of the dataset or model checkpoint.
2. **Component Type**: Categorized into `Training Dataset`, `Evaluation Dataset`, `Pre-trained Weights`, `Fine-tuned Weights`, or `Third-Party Dependency`.
3. **Source Provider / URL**: Official public URL or data provider repository.
4. **License & Usage Terms**: Legal license governing offline usage (e.g. CC BY 4.0, MIT, Apache 2.0, Open Data).
5. **SHA256 Checksum**: Cryptographic hash verifying file integrity and security against tampering.
6. **Ingestion Date**: Timestamp when the asset was downloaded and staged into local storage (`data/` or `models/`).
7. **Status**: Deployment state (`Staged`, `In-Use`, `Deprecated`, `Pending Ingestion`).

---

## 📊 Ingestion Audit Table

| Item Name | Component Type | Source Provider / URL | License | SHA256 Checksum | Ingestion Date | Status |
|---|---|---|---|---|---|---|
| RemoteCLIP (ViT-B/32) | Pre-trained Weights | HuggingFace / OpenCLIP | MIT | `PENDING_INGESTION` | - | Planned |
| RSICD Caption Dataset | Training Dataset | GitHub / RSICD Repository | Open Access | `PENDING_INGESTION` | - | Planned |
| LEVIR-CD | Change Detection Dataset | LEVIR Dataset Repository | CC BY 4.0 | `PENDING_INGESTION` | - | Planned |
| OSCD (Onera Satellite Change) | Change Detection Dataset | IEEE DataPort / ESA | CC BY-SA 4.0 | `PENDING_INGESTION` | - | Planned |
| Sentinel-2 AOI Samples | COG Earth Imagery | Copernicus Open Access Hub | Open Data | `PENDING_INGESTION` | - | Planned |

---

## 🛡️ Offline Air-Gap Verification Rule

Before deploying the platform in an offline environment:
1. Run `infra/scripts/stage_offline_deps.sh` to download and stage all required assets locally.
2. Compute the SHA256 checksum for each staged file and record it in the table above.
3. Validate that no external HTTP/S requests are made during runtime by executing `infra/scripts/test_offline_mode.sh`.
