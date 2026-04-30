# borderline_rd_input — v1 monolithic

**Latency:** 13.4s  
**Word count:** 308  
**Warning flag:** No

---

Existing open-source CDC implementations — including Debezium and Maxwell's Daemon — serialise schema evolution events through a centralised schema registry, introducing processing pauses when concurrent data definition language (DDL) events arrive during peak ingestion. Under the 2 million events-per-second load profile targeted by StreamBridge GmbH, these serialisation points produce latency spikes that violate the 50-millisecond end-to-end constraint. Flink's native schema evolution support does not address cross-source heterogeneity, and combining Kafka's log-compaction semantics with linearisable multi-source schema versioning remains an unsolved problem in published literature.

It cannot be established at the project's outset whether a lock-free schema-versioning mechanism can maintain linearisable consistency guarantees when concurrent DDL events arrive from heterogeneous source databases without introducing measurable throughput degradation. Specifically, the team cannot determine in advance whether optimistic concurrency control, applied at the CDC coordination layer, will produce sufficient conflict-detection accuracy under realistic DDL event distributions, or whether the consistency guarantees achievable under that model are operationally equivalent to strict linearisability.

To resolve these uncertainties, StreamBridge GmbH will implement and instrument two candidate consistency models — a lock-free optimistic versioning protocol and a hybrid vector-clock approach — deployed against a controlled Kafka-Flink pipeline. Synthetic load profiles derived from anonymised client event traces will drive each prototype through graduated DDL-concurrency scenarios. Success criteria are defined as sustained sub-50-millisecond end-to-end latency at 2 million events per second with zero linearisability violations across 10⁶ consecutive DDL-concurrent operations. Results from each experimental phase will determine whether the candidate model advances, is modified, or is abandoned in favour of the alternative, constituting a falsifiable, iterative investigation rather than incremental product construction.

---
*CONSULTANT NOTE: This document is a first draft prepared as a drafting aid by Ignite Group's application tooling. It does not constitute tax advice. A qualified consultant must review all technical claims, financial figures, and eligibility determinations before submission to the BSFZ or Finanzamt.*
