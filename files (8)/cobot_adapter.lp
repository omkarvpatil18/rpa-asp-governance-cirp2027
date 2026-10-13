%% ============================================================
%% cobot_adapter.lp
%% Domain adapter: Collaborative Robot (Cobot) Task Reallocation
%%
%% Translates raw shop-floor signals into the four governance
%% attributes (criticality, urgency, confidence, source).
%% This file must not modify governance_core.lp rules.
%%
%% External standards used:
%%   - ISO 10218-2:2011 (task safety classification)
%% ============================================================

%% ---- Criticality from ISO 10218-2 task safety class ---------
%%      safety_critical    -> 4 (safety-critical consequence)
%%      safety_adjacent    -> 2 (safety-adjacent consequence)
%%      non_safety         -> 1 (no safety consequence)

criticality(E, 4) :- task_class(E, safety_critical).
criticality(E, 2) :- task_class(E, safety_adjacent).
criticality(E, 1) :- task_class(E, non_safety).

%% ---- Urgency from remaining cycle-time budget (seconds) -----
%%      < 5s    -> 4 (immediate)
%%      5-30s   -> 3 (high)
%%      30-120s -> 2 (moderate)
%%      > 120s  -> 1 (low)

urgency(E, 4) :- cycle_budget(E, B), B < 5.
urgency(E, 3) :- cycle_budget(E, B), B >= 5,   B < 30.
urgency(E, 2) :- cycle_budget(E, B), B >= 30,  B < 120.
urgency(E, 1) :- cycle_budget(E, B), B >= 120.

%% ---- Confidence from task-detection model certainty ---------
%%      Passed through directly from sensor/model output [0,1].

confidence(E, K) :- detection_certainty(E, K).

%% ---- Source identifier for audit provenance -----------------

source(E, cobot_reallocation) :- event(E).
