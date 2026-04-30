# borderline_rd_input — v2 decomposed

**Latency:** 20.9s  
**Word count:** 324  
**Warning flag:** No

---

### Stage 1 — Failure mode

Existing CDC frameworks — including Debezium and Maxwell's Daemon — handle schema evolution through schema registry lookups and versioned serialisation formats such as Avro or Protobuf. Under concurrent DDL events, these frameworks introduce processing pauses by briefly halting consumer threads to resolve schema version conflicts before resuming event delivery. This pause-on-schema-change behaviour is acceptable at modest throughput but becomes a consistency and latency liability at two million events per second: queued events accumulate during the pause window, violating the sub-50-millisecond end-to-end latency target. No published lock-free alternative has demonstrated linearisable consistency guarantees under simultaneous DDL activity at this throughput scale.

### Stage 2 — Unknowns at outset

At the project's outset, it cannot be established whether a lock-free schema-versioning mechanism can maintain linearisable consistency guarantees under concurrent DDL events at two million events per second without introducing measurable processing pauses. It is unknown whether either of the two proposed consistency models will preserve sub-50-millisecond end-to-end latency under peak synthetic load, or whether throughput degradation will exceed acceptable thresholds when multiple DDL events occur simultaneously. The team cannot predict in advance which, if any, consistency model will converge to a stable operational state under the concurrent-write patterns derived from real client data, nor whether linearisability and throughput are simultaneously achievable at the target scale.

### Stage 3 — Synthesis

StreamBridge GmbH investigates whether a lock-free schema-versioning mechanism can maintain linearisable consistency guarantees under concurrent DDL events within an event-processing pipeline sustaining two million events per second, while preserving end-to-end latency below fifty milliseconds. This technical question is not resolved by existing publicly available methods. Established CDC frameworks, including Debezium and Maxwell's Daemon, address schema evolution through schema registry lookups combined with versioned serialisation formats such as Avro or Protobuf. Under concurrent DDL activity, these frameworks resolve schema version conflicts by halting consumer threads, introducing processing pauses that cause event accumulation and latency violations at the target throughput scale. No published lock-free alternative has demonstrated linearisable consistency under simultaneous DDL events at two million events per second without measurable pause behaviour.

At the project's outset, it cannot be established whether any lock-free consistency model will simultaneously satisfy linearisability requirements and the sub-fifty-millisecond latency target under the concurrent-write patterns present in real client workloads. It is unknown whether throughput degradation under multiple simultaneous DDL events will remain within acceptable operational bounds, and the team cannot predict in advance whether either proposed consistency model will converge to a stable operational state under peak synthetic load conditions.

To address these uncertainties systematically, the project defines two candidate consistency models, each representing a distinct architectural trade-off between coordination overhead and consistency strength. Both models are subjected to controlled synthetic load profiles derived from real client data, with explicit measurable success criteria for latency, throughput, and consistency. Outcomes at each experimental stage are evaluated against pre-defined thresholds, and the methodology is updated accordingly. The knowledge produced is applicable to any high-throughput stream-processing architecture requiring schema evolution without processing interruption.

---

**CONSULTANT NOTE:** This is a first draft produced by an AI drafting aid and does not constitute tax or legal advice. A qualified consultant must review this statement for technical accuracy, alignment with the applicant's actual methodology, and compliance with current BSFZ submission requirements before any submission is made.
