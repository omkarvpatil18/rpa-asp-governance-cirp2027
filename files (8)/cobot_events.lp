%% ============================================================
%% cobot_events.lp
%% Test events for the Cobot Task Reallocation domain
%%
%% Events CB-01 to CB-07 cover all four priority tiers,
%% both sides of the confidence threshold, the dismissal
%% floor edge case, and the policy maintainability boundary.
%%
%% Expected outcomes:
%%   CB-01: autonomous  (Routine, high confidence)
%%   CB-02: autonomous  (Elevated, high confidence)
%%   CB-03: escalate    (Priority, high confidence) -> high priority
%%   CB-04: escalate    (Critical, high confidence) -> high priority
%%   CB-05: escalate    (Priority, low confidence)  -> low confidence
%%   CB-06: autonomous  (Routine, low confidence)   -> below dismissal floor
%%   CB-07: escalate    (Priority, boundary)        -> policy test event
%% ============================================================

%% ---- CB-01: Routine, high confidence -> autonomous ----------
event(cb01).
task_class(cb01, non_safety).       %% criticality -> 1
cycle_budget(cb01, 200).            %% urgency     -> 1 (> 120s)
detection_certainty(cb01, 0.90).    %% confidence  -> 0.90

%% ---- CB-02: Elevated, high confidence -> autonomous ---------
event(cb02).
task_class(cb02, safety_adjacent).  %% criticality -> 2
cycle_budget(cb02, 45).             %% urgency     -> 2 (30-120s)
detection_certainty(cb02, 0.80).    %% confidence  -> 0.80

%% ---- CB-03: Priority, high confidence -> escalate (R3) ------
event(cb03).
task_class(cb03, safety_adjacent).  %% criticality -> 2
cycle_budget(cb03, 12).             %% urgency     -> 3 (5-30s)
detection_certainty(cb03, 0.75).    %% confidence  -> 0.75

%% ---- CB-04: Critical, high confidence -> escalate (R3) ------
event(cb04).
task_class(cb04, safety_critical).  %% criticality -> 4
cycle_budget(cb04, 3).              %% urgency     -> 4 (< 5s)
detection_certainty(cb04, 0.85).    %% confidence  -> 0.85

%% ---- CB-05: Priority, low confidence -> escalate (R2) -------
event(cb05).
task_class(cb05, safety_adjacent).  %% criticality -> 2
cycle_budget(cb05, 12).             %% urgency     -> 3 (5-30s)
detection_certainty(cb05, 0.40).    %% confidence  -> 0.40 (below theta_k)

%% ---- CB-06: Routine, low confidence -> autonomous -----------
%%      Tests dismissal floor: Routine tier (1) does not exceed
%%      theta_d (1), so R2 does not fire despite low confidence.
event(cb06).
task_class(cb06, non_safety).       %% criticality -> 1
cycle_budget(cb06, 35).             %% urgency     -> 2 (30-120s)
detection_certainty(cb06, 0.30).    %% confidence  -> 0.30 (below theta_k)

%% ---- CB-07: Priority boundary -> policy maintainability test -
%%      Sits at Priority tier with confidence above threshold.
%%      Escalates when theta_p = Priority (3).
%%      Becomes autonomous when theta_p raised to Critical (4).
event(cb07).
task_class(cb07, safety_adjacent).  %% criticality -> 2
cycle_budget(cb07, 8).              %% urgency     -> 3 (5-30s)
detection_certainty(cb07, 0.70).    %% confidence  -> 0.70 (above theta_k)
