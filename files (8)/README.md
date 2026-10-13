# Declarative Governance for Autonomous Decision-Making in Deep Tech Manufacturing Ecosystems

**Paper:** Declarative Governance for Autonomous Decision-Making in Deep Tech Manufacturing
Ecosystems using Robotic Process Automation and Answer Set Programming

**Authors:** Omkar Vishwas Patil, Omid Fatahi Valilai

**Affiliation:** Emerging Technologies in Industrial Engineering (EITIE) Research Group,
School of Business, Social & Decision Sciences, Constructor University Bremen, Germany

**Conference:** 60th CIRP Conference on Manufacturing Systems (CIRP CMS 2027)

---

## Repository Structure

```
repository/
│
├── core/
│   ├── governance_core.lp        # Domain-independent ASP governance rules (R1-R4)
│   └── priority_matrix.lp        # Priority matrix facts and threshold configuration
│
├── adapters/
│   ├── cobot_adapter.lp          # Cobot task reallocation domain adapter
│   └── scheduling_adapter.lp     # Sustainable scheduling exception domain adapter
│
├── test_events/
│   ├── cobot/
│   │   └── cobot_events.lp       # All 7 test events for cobot domain (CB-01 to CB-07)
│   └── scheduling/
│       └── scheduling_events.lp  # All 7 test events for scheduling domain (SS-01 to SS-07)
│
├── results/
│   └── verification.md           # Hand-verified expected vs actual outcomes
│
└── README.md
```

---

## Requirements

- [clingo](https://potassco.org/clingo/) version 5.8.2 or later

Install via:
```bash
pip install clingo
```

---

## Running the Governance Core

### Cobot Task Reallocation

Run all test events:
```bash
clingo core/governance_core.lp core/priority_matrix.lp adapters/cobot_adapter.lp test_events/cobot/cobot_events.lp
```

Run a single event (e.g. CB-03):
```bash
clingo core/governance_core.lp core/priority_matrix.lp adapters/cobot_adapter.lp test_events/cobot/cobot_events.lp --const event=cb03
```

### Sustainable Scheduling Exception

Run all test events:
```bash
clingo core/governance_core.lp core/priority_matrix.lp adapters/scheduling_adapter.lp test_events/scheduling/scheduling_events.lp
```

---

## Policy Change Test

To reproduce the policy maintainability result (raising theta_p from Priority to Critical),
edit `core/priority_matrix.lp` and change:

```
#const theta_p = 3.  % Priority
```
to:
```
#const theta_p = 4.  % Critical
```

Then rerun both domains. Boundary events CB-07 and SS-07 should move from
`escalate` to `autonomous` with no adapter modification.

---

## Licence

This repository is released under the MIT Licence.
