# Verification of Governance Outcomes

All solver outputs were independently verified by hand computation
against the priority matrix and confidence gate specification.

## Thresholds Used

| Threshold | Value | Meaning |
|---|---|---|
| theta_k | 0.6 | Confidence gate threshold |
| theta_d | 1 (Routine) | Dismissal floor |
| theta_p | 3 (Priority) | Escalation tier threshold |

## Cobot Task Reallocation Domain

| Event | C | U | K | Tier | Rule Fired | Expected | Actual | Match |
|---|---|---|---|---|---|---|---|---|
| CB-01 | 1 | 1 | 0.90 | Routine (1) | R4 | autonomous | autonomous | YES |
| CB-02 | 2 | 2 | 0.80 | Elevated (2) | R4 | autonomous | autonomous | YES |
| CB-03 | 2 | 3 | 0.75 | Priority (3) | R3 | escalate | escalate | YES |
| CB-04 | 4 | 4 | 0.85 | Critical (4) | R3 | escalate | escalate | YES |
| CB-05 | 2 | 3 | 0.40 | Priority (3) | R2 | escalate | escalate | YES |
| CB-06 | 1 | 2 | 0.30 | Routine (1) | R4 | autonomous | autonomous | YES |
| CB-07 | 2 | 3 | 0.70 | Priority (3) | R3 | escalate | escalate | YES |

**CB-06 dismissal floor check:**
K=0.30 < theta_k=0.6 BUT Tier=1 NOT > theta_d=1, so R2 does NOT fire.
R3 requires Tier >= 3, not satisfied. Therefore R4 fires: autonomous. CORRECT.

**CB-05 vs CB-07 distinction:**
CB-05: escalated via R2 (low confidence). Audit reason: escalate_low_confidence.
CB-07: escalated via R3 (high priority). Audit reason: escalate_high_priority.
Records are distinguishable. CORRECT.

## Sustainable Scheduling Exception Domain

| Event | C | U | K | Tier | Rule Fired | Expected | Actual | Match |
|---|---|---|---|---|---|---|---|---|
| SS-01 | 1 | 1 | 0.95 | Routine (1) | R4 | autonomous | autonomous | YES |
| SS-02 | 2 | 2 | 0.82 | Elevated (2) | R4 | autonomous | autonomous | YES |
| SS-03 | 3 | 3 | 0.78 | Priority (3) | R3 | escalate | escalate | YES |
| SS-04 | 4 | 4 | 0.91 | Critical (4) | R3 | escalate | escalate | YES |
| SS-05 | 3 | 3 | 0.35 | Priority (3) | R2 | escalate | escalate | YES |
| SS-06 | 1 | 1 | 0.25 | Routine (1) | R4 | autonomous | autonomous | YES |
| SS-07 | 3 | 3 | 0.72 | Priority (3) | R3 | escalate | escalate | YES |

**SS-06 dismissal floor check:**
K=0.25 < theta_k=0.6 BUT Tier=1 NOT > theta_d=1, so R2 does NOT fire.
R3 requires Tier >= 3, not satisfied. Therefore R4 fires: autonomous. CORRECT.

## Policy Maintainability Test

Changing theta_p from 3 (Priority) to 4 (Critical) in priority_matrix.lp:

| Event | Tier | K | Old outcome | New outcome | Adapter changed |
|---|---|---|---|---|---|
| CB-07 | Priority (3) | 0.70 | escalate | autonomous | NO |
| SS-07 | Priority (3) | 0.72 | escalate | autonomous | NO |

Single edit to shared core. Zero adapter modifications. CORRECT.

## Summary

| Domain | Conformance | Audit complete | Adapter size | Ratio |
|---|---|---|---|---|
| Cobot Reallocation | 7/7 | 7/7 | 11 statements | 0.478 |
| Sustainable Scheduling | 7/7 | 7/7 | 11 statements | 0.478 |
| **Total** | **14/14** | **14/14** | **11 each** | **Identical** |

Core size: 23 statements (4 rules + 19 matrix and threshold facts).
Adapter-to-core ratio: 11/23 = 0.478.
