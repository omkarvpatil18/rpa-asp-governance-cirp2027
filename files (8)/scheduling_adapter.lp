%% ============================================================
%% scheduling_adapter.lp
%% Domain adapter: Sustainable Production Scheduling Exception
%%
%% Translates sustainability breach signals into the four
%% governance attributes (criticality, urgency, confidence, source).
%% This file must not modify governance_core.lp rules.
%% ============================================================

%% ---- Criticality from breach type ---------------------------
%%      hard_contractual_cap    -> 4 (compliance-critical)
%%      regulatory_threshold    -> 3 (regulatory breach)
%%      soft_target             -> 2 (internal target breach)
%%      advisory                -> 1 (advisory only)

criticality(E, 4) :- breach_type(E, hard_contractual_cap).
criticality(E, 3) :- breach_type(E, regulatory_threshold).
criticality(E, 2) :- breach_type(E, soft_target).
criticality(E, 1) :- breach_type(E, advisory).

%% ---- Urgency from time to constraint violation (minutes) ----
%%      < 1 min    -> 4 (immediate)
%%      1-15 min   -> 3 (high)
%%      15-60 min  -> 2 (moderate)
%%      > 60 min   -> 1 (low)

urgency(E, 4) :- time_to_violation(E, T), T < 1.
urgency(E, 3) :- time_to_violation(E, T), T >= 1,  T < 15.
urgency(E, 2) :- time_to_violation(E, T), T >= 15, T < 60.
urgency(E, 1) :- time_to_violation(E, T), T >= 60.

%% ---- Confidence from sensor data completeness/recency -------
%%      Passed through directly as a score in [0,1].

confidence(E, K) :- data_quality_score(E, K).

%% ---- Source identifier for audit provenance -----------------

source(E, sustainable_scheduling) :- event(E).
