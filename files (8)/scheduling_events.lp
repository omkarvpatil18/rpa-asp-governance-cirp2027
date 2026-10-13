%% ============================================================
%% scheduling_events.lp
%% Test events for the Sustainable Scheduling Exception domain
%%
%% Events SS-01 to SS-07 cover all four priority tiers,
%% both sides of the confidence threshold, the dismissal
%% floor edge case, and the policy maintainability boundary.
%%
%% Expected outcomes:
%%   SS-01: autonomous  (Routine, high confidence)
%%   SS-02: autonomous  (Elevated, high confidence)
%%   SS-03: escalate    (Priority, high confidence) -> high priority
%%   SS-04: escalate    (Critical, high confidence) -> high priority
%%   SS-05: escalate    (Priority, low confidence)  -> low confidence
%%   SS-06: autonomous  (Routine, low confidence)   -> below dismissal floor
%%   SS-07: escalate    (Priority, boundary)        -> policy test event
%% ============================================================

%% ---- SS-01: Routine, high confidence -> autonomous ----------
event(ss01).
breach_type(ss01, advisory).        %% criticality -> 1
time_to_violation(ss01, 90).        %% urgency     -> 1 (> 60 min)
data_quality_score(ss01, 0.95).     %% confidence  -> 0.95

%% ---- SS-02: Elevated, high confidence -> autonomous ---------
event(ss02).
breach_type(ss02, soft_target).     %% criticality -> 2
time_to_violation(ss02, 30).        %% urgency     -> 2 (15-60 min)
data_quality_score(ss02, 0.82).     %% confidence  -> 0.82

%% ---- SS-03: Priority, high confidence -> escalate (R3) ------
event(ss03).
breach_type(ss03, regulatory_threshold). %% criticality -> 3
time_to_violation(ss03, 8).         %% urgency     -> 3 (1-15 min)
data_quality_score(ss03, 0.78).     %% confidence  -> 0.78

%% ---- SS-04: Critical, high confidence -> escalate (R3) ------
event(ss04).
breach_type(ss04, hard_contractual_cap). %% criticality -> 4
time_to_violation(ss04, 0.5).       %% urgency     -> 4 (< 1 min)
data_quality_score(ss04, 0.91).     %% confidence  -> 0.91

%% ---- SS-05: Priority, low confidence -> escalate (R2) -------
event(ss05).
breach_type(ss05, regulatory_threshold). %% criticality -> 3
time_to_violation(ss05, 10).        %% urgency     -> 3 (1-15 min)
data_quality_score(ss05, 0.35).     %% confidence  -> 0.35 (below theta_k)

%% ---- SS-06: Routine, low confidence -> autonomous -----------
%%      Tests dismissal floor: Routine tier (1) does not exceed
%%      theta_d (1), so R2 does not fire despite low confidence.
event(ss06).
breach_type(ss06, advisory).        %% criticality -> 1
time_to_violation(ss06, 120).       %% urgency     -> 1 (> 60 min)
data_quality_score(ss06, 0.25).     %% confidence  -> 0.25 (below theta_k)

%% ---- SS-07: Priority boundary -> policy maintainability test -
%%      Sits at Priority tier with confidence above threshold.
%%      Escalates when theta_p = Priority (3).
%%      Becomes autonomous when theta_p raised to Critical (4).
event(ss07).
breach_type(ss07, regulatory_threshold). %% criticality -> 3
time_to_violation(ss07, 6).         %% urgency     -> 3 (1-15 min)
data_quality_score(ss07, 0.72).     %% confidence  -> 0.72 (above theta_k)
