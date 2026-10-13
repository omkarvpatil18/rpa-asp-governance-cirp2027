%% ============================================================
%% priority_matrix.lp
%% Priority matrix facts and governance threshold configuration
%%
%% Tiers: 1=Routine, 2=Elevated, 3=Priority, 4=Critical
%% Modify thresholds here to update governance policy.
%% No adapter file needs to change when thresholds are updated.
%% ============================================================

%% ---- Priority matrix: matrix(Criticality, Urgency, Tier) ----
%%      Rows = Criticality (1-4), Columns = Urgency (1-4)

matrix(1, 1, 1).  % R
matrix(1, 2, 1).  % R
matrix(1, 3, 2).  % E
matrix(1, 4, 2).  % E

matrix(2, 1, 1).  % R
matrix(2, 2, 2).  % E
matrix(2, 3, 3).  % P
matrix(2, 4, 3).  % P

matrix(3, 1, 2).  % E
matrix(3, 2, 3).  % P
matrix(3, 3, 3).  % P
matrix(3, 4, 4).  % X

matrix(4, 1, 2).  % E
matrix(4, 2, 3).  % P
matrix(4, 3, 4).  % X
matrix(4, 4, 4).  % X

%% ---- Thresholds (policy configuration) ----------------------

%% theta_k: confidence threshold below which a signal is
%%          considered unreliable for autonomous action.
#const theta_k = 0.6.

%% theta_d: dismissal floor — tier must EXCEED this value for
%%          R2 (low-confidence escalation) to fire.
%%          Value 1 = Routine: Routine-tier uncertain events
%%          are never escalated solely for low confidence.
#const theta_d = 1.

%% theta_p: escalation tier threshold — events at or above
%%          this tier are escalated regardless of confidence.
%%          3 = Priority. Change to 4 (Critical) to tighten policy.
#const theta_p = 3.
