%% ============================================================
%% governance_core.lp
%% Domain-independent declarative governance core
%%
%% Paper: Declarative Governance for Autonomous Decision-Making
%%        in Deep Tech Manufacturing Ecosystems using RPA and ASP
%% Authors: Omkar Vishwas Patil, Omid Fatahi Valilai
%% Conference: CIRP CMS 2027
%%
%% This file contains the four governance rules (R1-R4).
%% It must not be modified for domain-specific instantiation.
%% Domain adaptation is handled exclusively by adapter files.
%% ============================================================

%% R1 - Derive priority tier from criticality, urgency, and the
%%      configurable 4x4 priority matrix (defined in priority_matrix.lp).
%%      Tier T is one of: 1=Routine, 2=Elevated, 3=Priority, 4=Critical.
priority(E, T) :-
    criticality(E, C),
    urgency(E, U),
    matrix(C, U, T).

%% R2 - Escalate if confidence falls below threshold theta_k AND
%%      the priority tier exceeds the dismissal floor theta_d.
%%      The dismissal floor prevents indiscriminate escalation of
%%      uncertain but genuinely low-stakes signals.
escalate(E) :-
    confidence(E, K),
    K < theta_k,
    priority(E, T),
    T > theta_d.

%% R3 - Escalate unconditionally if the priority tier meets or
%%      exceeds the escalation threshold theta_p, regardless of
%%      signal confidence.
escalate(E) :-
    priority(E, T),
    T >= theta_p.

%% R4 - Permit autonomous execution only when no escalation
%%      condition holds (negation-as-failure over stratified
%%      derivation; no circularity arises).
autonomous(E) :-
    priority(E, T),
    confidence(E, K),
    not escalate(E).

%% ============================================================
%% Audit record: produced as a direct output of reasoning.
%% Records attributes, tier, outcome, and escalation reason.
%% ============================================================

audit(E, C, U, K, S, T, escalate_low_confidence) :-
    escalate(E),
    criticality(E, C), urgency(E, U), confidence(E, K),
    source(E, S), priority(E, T),
    K < theta_k, T > theta_d.

audit(E, C, U, K, S, T, escalate_high_priority) :-
    escalate(E),
    criticality(E, C), urgency(E, U), confidence(E, K),
    source(E, S), priority(E, T),
    T >= theta_p,
    not (K < theta_k, T > theta_d).

audit(E, C, U, K, S, T, autonomous_proceed) :-
    autonomous(E),
    criticality(E, C), urgency(E, U), confidence(E, K),
    source(E, S), priority(E, T).

%% Display
#show audit/7.
#show priority/2.
#show escalate/1.
#show autonomous/1.
