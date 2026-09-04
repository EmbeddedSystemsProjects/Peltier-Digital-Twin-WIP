%% run_final_simulation.m
% Simulazione finale Digital Twin Peltier per il report
%
% FASE 1 - Legge la configurazione attuale dal modello Simulink
% FASE 2 - Esegue la simulazione matematica (Eulero 1s, no Simulink)
% FASE 3 - Confronta con i dati reali (CSV)
% FASE 4 - Genera figure qualità report (300 DPI, font 12pt, italiano)
%
% Output:
%   fig_risultati_sim.png   — T_fredda/calda simulazione vs reale + setpoints
%   fig_pid_confronto.png   — Output PID e tensione/corrente cella
%   Risultati_Sim_Finale.csv — dati numerici completi

clear; clc; close all;

fprintf('============================================================\n');
fprintf('  run_final_simulation.m  –  Simulazione Finale Report\n');
fprintf('============================================================\n\n');

%% ══════════════════════════════════════════════════════════════════
%  FASE 1 — LEGGI CONFIGURAZIONE SIMULINK
% ══════════════════════════════════════════════════════════════════
fprintf('--- FASE 1: Lettura configurazione Simulink ---\n');
mdl = 'Peltier_DigitalTwin';
mdl_ok = false;
try
    load_system(mdl);
    mdl_ok = true;
    fprintf('[OK] Modello caricato: %s\n', mdl);
catch
    fprintf('[!] Modello Simulink non trovato — uso parametri di default\n');
end

% Valori di default (post fix_pid_scaling.m)
cfg.V_PWM_max = 1;    % duty cycle puro
cfg.V_DAC_max = 100;  % SetOutputLimits(0,100)
cfg.V_in_max  = 6;    % alimentazione TPS54618
cfg.PID_lo    = 0;
cfg.PID_hi    = 100;
cfg.Kp        = 0.5;
cfg.Ki        = 0.01;
cfg.Kd        = 0.0;

if mdl_ok
    % Leggi parametri dal modello
    params_da_leggere = {'V_PWM_max','V_DAC_max','V_in_max'};
    for k = 1:numel(params_da_leggere)
        try
            val = str2double(get_param([mdl '/' params_da_leggere{k}], 'Value'));
            cfg.(params_da_leggere{k}) = val;
        catch; end
    end

    % Leggi saturazione PID
    pid_sub = find_system(mdl, 'Name', 'Controllore PID');
    if ~isempty(pid_sub)
        try
            cfg.PID_lo = str2double(get_param(pid_sub{1}, 'LowerSaturationLimit'));
            cfg.PID_hi = str2double(get_param(pid_sub{1}, 'UpperSaturationLimit'));
        catch; end
        % Kp/Ki/Kd: NON letti dal modello Simulink — i param mask del subsystem custom
        % non espongono i guadagni reali. Si usano i valori del firmware (da Driver_FW.ino):
        %   Kp=0.5, Ki=0.01, Kd=0  (verificati su CSV: output t=241s = 1.1 = 0.5*(24.08-22))
    end

    % Leggi profilatore
    try
        lr_str = get_param([mdl '/Lista Rampe'],     'Value');
        ls_str = get_param([mdl '/Lista Setpoints'], 'Value');
        fprintf('[OK] Profilatore letto dal modello\n');
        fprintf('     Lista Rampe     = %s\n', lr_str(1:min(60,end)));
        fprintf('     Lista Setpoints = %s\n', ls_str);
    catch
        fprintf('[!] Profilatore: blocchi non trovati\n');
    end

    % Leggi I_max (cerca nel modello)
    try
        I_lim_blk = find_system(mdl, 'Name', 'I_lim');
        if ~isempty(I_lim_blk)
            cfg.I_max = str2double(get_param(I_lim_blk{1}, 'Value'));
            fprintf('[OK] I_lim = %.1f A\n', cfg.I_max);
        end
    catch; end
end

% Riepilogo configurazione
fprintf('\n=== Configurazione sistema ===\n');
fprintf('  V_supply  = %.1f V      (TPS54618 output)\n', cfg.V_in_max);
fprintf('  PID range = [%.0f, %.0f]  (SetOutputLimits)\n', cfg.PID_lo, cfg.PID_hi);
fprintf('  Kp=%.2f  Ki=%.3f  Kd=%.1f\n', cfg.Kp, cfg.Ki, cfg.Kd);
fprintf('  V_cella   = (PID/%.0f) * %.1f V  ← uguale al firmware\n', cfg.PID_hi, cfg.V_in_max);
if isfield(cfg,'I_max'), fprintf('  I_max     = %.1f A\n', cfg.I_max); end
fprintf('\n');

%% ══════════════════════════════════════════════════════════════════
%  FASE 2 — SIMULAZIONE (Eulero 1s, parametri identificati)
% ══════════════════════════════════════════════════════════════════
fprintf('--- FASE 2: Simulazione matematica ---\n');

% Parametri cella (misurati)
alpha   = 0.0152;   % [V/K]
R_cell  = 2.04;     % [Ohm]
K_cell  = 0.52;     % [W/K]
I_max   = 4.0;      % [A]

% Parametri termici (stimati da RIPOSO1, vedi memoria)
C_f     = 587.0;    % [J/K]  lato freddo
C_h     = 1419.0;   % [J/K]  lato caldo
K_iso_f = 0.1;      % [W/K]
K_iso_h = 0.1;      % [W/K]
T_amb   = 24.0;     % [°C]

% Profilo esatto dal CSV (firmware: T_SP1_START=300s, TIME_WAIT_BOOT=60s)
T_START = [  0,  240, 2040, 2940, 4740, 5640];
T_END   = [240, 2040, 2940, 4740, 5640, 6840];
SP_VAL  = [NaN,   22,  NaN,   20,  NaN,   18];
NOME    = {'STANDBY','SP1=22','RIPOSO1','SP2=20','RIPOSO2','SP3=18'};
N_FASI  = 6;  N_STEP = 6840;

% Pre-calcola fase per ogni istante
t_sim = (0:N_STEP)';
fase_vec = zeros(N_STEP+1,1);
for k = 1:N_STEP+1
    fi = find(t_sim(k) >= T_START & t_sim(k) < T_END, 1);
    if isempty(fi), fi = N_FASI; end
    fase_vec(k) = fi;
end

% Alloca
Tf_s  = zeros(N_STEP+1,1);  Tc_s  = zeros(N_STEP+1,1);
V_s   = zeros(N_STEP+1,1);  I_s   = zeros(N_STEP+1,1);
pid_s = zeros(N_STEP+1,1);  sp_s  = NaN(N_STEP+1,1);
Tf_s(1)=T_amb; Tc_s(1)=T_amb; sp_s(1)=SP_VAL(fase_vec(1));
ITerm=0.0; pid_out=0.0;

tic;
for k = 1:N_STEP
    fi=fase_vec(k); sp=SP_VAL(fi);
    if k>1 && fi~=fase_vec(k-1), ITerm=0.0; end
    if isnan(sp)
        pid_out=0.0; ITerm=0.0;
    else
        err    = Tf_s(k) - sp;
        ITerm  = min(cfg.PID_hi, max(cfg.PID_lo, ITerm + cfg.Ki*err));
        pid_out= min(cfg.PID_hi, max(cfg.PID_lo, cfg.Kp*err + ITerm));
    end
    V_c = (pid_out/cfg.PID_hi)*cfg.V_in_max;
    I_c = min(I_max, max(0, V_c/R_cell));
    Tf_K=Tf_s(k)+273.15; Tc_K=Tc_s(k)+273.15; dT=Tc_s(k)-Tf_s(k);
    Qc  = alpha*I_c*Tf_K - 0.5*R_cell*I_c^2 - K_cell*dT;
    Qh  = alpha*I_c*Tc_K + 0.5*R_cell*I_c^2 - K_cell*dT;
    Tf_s(k+1)  = Tf_s(k)+(-Qc+K_iso_f*(T_amb-Tf_s(k)))/C_f;
    Tc_s(k+1)  = Tc_s(k)+(Qh-K_iso_h*(Tc_s(k)-T_amb))/C_h;
    V_s(k+1)=V_c; I_s(k+1)=I_c; pid_s(k+1)=pid_out; sp_s(k+1)=sp;
end
fprintf('[OK] Simulazione completata in %.2fs\n\n', toc);

%% ══════════════════════════════════════════════════════════════════
%  FASE 3 — CARICA CSV REALE
% ══════════════════════════════════════════════════════════════════
fprintf('--- FASE 3: Caricamento dati reali ---\n');
HERE     = fileparts(mfilename('fullpath'));
FIGURES  = fullfile(HERE,'..','..','figures');
if ~exist(FIGURES,'dir'), mkdir(FIGURES); end
csv_path = fullfile(HERE,'..','dataset','test_peltier_20260620_095618.csv');
has_real = false;
if exist(csv_path,'file')
    try
        T_real = readtable(csv_path,'TextType','string');
        t_r   = double(T_real{:,1})/1000;
        Tf_r  = double(T_real{:,3});
        Tc_r  = double(T_real{:,4});
        pid_r = double(T_real{:,5});
        ok    = ~isnan(t_r) & ~isnan(Tf_r);
        t_r=t_r(ok); Tf_r=Tf_r(ok); Tc_r=Tc_r(ok); pid_r=pid_r(ok);
        has_real = true;
        fprintf('[OK] CSV: %d campioni, t=[%.0fs, %.0fs]\n\n', sum(ok), t_r(1), t_r(end));
    catch ME
        fprintf('[!] %s\n\n', ME.message);
    end
else
    fprintf('[!] CSV non trovato: %s\n\n', csv_path);
end

%% ══════════════════════════════════════════════════════════════════
%  FASE 4 — FIGURE REPORT (alta risoluzione)
% ══════════════════════════════════════════════════════════════════
fprintf('--- FASE 4: Generazione figure ---\n');

% Stile grafico comune
set(0,'DefaultAxesFontSize',12,'DefaultAxesFontName','Arial');
set(0,'DefaultLineLineWidth',1.5);
set(0,'DefaultAxesLineWidth',0.8);

% Palette colori
COL.sim_f = [0.07 0.45 0.70];   % blu       → T_fredda sim
COL.sim_h = [0.85 0.33 0.10];   % rosso     → T_calda sim
COL.re_f  = [0.25 0.70 0.25];   % verde     → T_fredda reale
COL.re_h  = [0.93 0.69 0.13];   % arancio   → T_calda reale
COL.sp    = [0.0  0.0  0.0];    % nero      → setpoint
COL.riposo= [0.94 0.94 0.97];   % grigio ch.→ sfondo fasi riposo

% Asse x in minuti
t_min_s  = t_sim/60;
if has_real, t_min_r = t_r/60; end
xL_min   = T_END(1:end-1)/60;

% ── FIGURA 1: Temperature ──────────────────────────────────────────
fig1 = figure('Units','centimeters','Position',[2 2 18 13],'Color','w');
ax1  = axes(fig1,'Position',[0.10 0.42 0.87 0.55]);
hold on; grid on; box on;

% Sfondo fasi RIPOSO
for i=[3 5]
    fill([T_START(i) T_END(i) T_END(i) T_START(i)]/60, [10 10 50 50], ...
        COL.riposo,'EdgeColor','none','HandleVisibility','off');
end

% Setpoint (scalini)
stairs(t_min_s, sp_s, '--', 'Color',COL.sp, 'LineWidth',1.2, 'DisplayName','Setpoint');

% Simulazione
plot(t_min_s, Tf_s, '-', 'Color',COL.sim_f, 'LineWidth',2.0, 'DisplayName','T_{fredda} – Sim.');
plot(t_min_s, Tc_s, '-', 'Color',COL.sim_h, 'LineWidth',2.0, 'DisplayName','T_{calda} – Sim.');

% Dati reali
if has_real
    plot(t_min_r, Tf_r, '--', 'Color',COL.re_f, 'LineWidth',1.2, 'DisplayName','T_{fredda} – Reale');
    plot(t_min_r, Tc_r, '--', 'Color',COL.re_h, 'LineWidth',1.2, 'DisplayName','T_{calda} – Reale');
end

for xv=xL_min; xline(xv,':','Color',[0.6 0.6 0.6],'LineWidth',0.8,'HandleVisibility','off'); end

ylabel('Temperatura [°C]','FontSize',12);
title('Digital Twin Peltier – Confronto simulazione vs misura reale','FontSize',13,'FontWeight','bold');
legend('Location','northeast','FontSize',9,'NumColumns',2);
xlim([0 N_STEP/60]); ylim([15 50]);
xticks(0:10:120); grid minor;

% Etichette fasi
y_lab = 48;
for i=1:N_FASI
    text((T_START(i)+T_END(i))/2/60, y_lab, strrep(NOME{i},'=','='), ...
        'HorizontalAlignment','center','FontSize',9,'Color',[0.35 0.35 0.35], ...
        'FontAngle','italic');
end

% Pannello statistiche a destra in basso
ax2 = axes(fig1,'Position',[0.10 0.06 0.87 0.30]);
hold on; grid on; box on;

% Errore Tf_sim − Tf_reale
if has_real
    Tf_sim_interp = interp1(t_sim, Tf_s, t_r, 'linear','extrap');
    err_Tf = Tf_sim_interp - Tf_r;
    plot(t_min_r, err_Tf, '-', 'Color',COL.sim_f, 'LineWidth',1.2);
    yline(0,'k:','LineWidth',0.8);
    % Shade ±1K
    fill([0 N_STEP/60 N_STEP/60 0], [-1 -1 1 1], [0.9 0.9 1], 'EdgeColor','none','FaceAlpha',0.5);
    ylabel('\Delta T_{fredda} [K]','FontSize',11);
    xlabel('Tempo [min]','FontSize',12);
    ylim([-6 6]); xlim([0 N_STEP/60]);
    for xv=xL_min; xline(xv,':','Color',[0.6 0.6 0.6],'LineWidth',0.8); end
    title('Errore simulazione: T_{fredda,sim} − T_{fredda,reale}','FontSize',11);
else
    text(0.5,0.5,'Dati CSV reale non disponibili','HorizontalAlignment','center',...
        'Units','normalized','FontSize',11,'Color',[0.5 0.5 0.5]);
    xlabel('Tempo [min]','FontSize',12);
end

print(fig1, fullfile(FIGURES,'fig_risultati_sim.png'), '-dpng', '-r300');
fprintf('[OK] figures/fig_risultati_sim.png\n');

% ── FIGURA 2: PID + V/I ───────────────────────────────────────────
fig2 = figure('Units','centimeters','Position',[2 2 18 12],'Color','w');

sp2a = subplot(2,1,1);
hold on; grid on; box on;
plot(t_min_s, pid_s, '-', 'Color',COL.sim_f, 'LineWidth',1.8, 'DisplayName','PID – Sim.');
if has_real
    plot(t_min_r, pid_r, '--', 'Color',COL.re_f, 'LineWidth',1.2, 'DisplayName','PID – Reale');
end
for xv=xL_min; xline(xv,':','Color',[0.6 0.6 0.6],'LineWidth',0.8,'HandleVisibility','off'); end
ylabel('Uscita PID [0–100]','FontSize',12);
title('Segnale di controllo PID','FontSize',12,'FontWeight','bold');
legend('Location','northeast','FontSize',9); ylim([-2 105]); xlim([0 N_STEP/60]);
grid minor;

sp2b = subplot(2,1,2);
hold on; grid on; box on;
yyaxis left
plot(t_min_s, V_s, '-', 'Color',COL.sim_f, 'LineWidth',1.8, 'DisplayName','V_{cella}');
ylabel('V_{cella} [V]','FontSize',12);
yyaxis right
plot(t_min_s, I_s, '-', 'Color',COL.sim_h, 'LineWidth',1.8, 'DisplayName','I_{cella}');
ylabel('I_{cella} [A]','FontSize',12);
for xv=xL_min; xline(xv,':','Color',[0.6 0.6 0.6],'LineWidth',0.8,'HandleVisibility','off'); end
xlabel('Tempo [min]','FontSize',12);
title('Tensione e corrente cella Peltier','FontSize',12,'FontWeight','bold');
xlim([0 N_STEP/60]); grid minor;

linkaxes([sp2a sp2b],'x');
print(fig2, fullfile(FIGURES,'fig_pid_confronto.png'), '-dpng', '-r300');
fprintf('[OK] figures/fig_pid_confronto.png\n\n');

%% ══════════════════════════════════════════════════════════════════
%  SALVA CSV
% ══════════════════════════════════════════════════════════════════
sp_csv = sp_s; sp_csv(isnan(sp_s)) = 0;
writetable(table(t_sim, sp_csv, Tf_s, Tc_s, V_s, I_s, pid_s, ...
    'VariableNames',{'time_s','Setpoint_C','T_fredda_C','T_calda_C','V_cella_V','I_cella_A','PID_output'}), ...
    fullfile(FIGURES,'Risultati_Sim_Finale.csv'));
fprintf('[OK] figures/Risultati_Sim_Finale.csv\n\n');

%% ══════════════════════════════════════════════════════════════════
%  TABELLA STATISTICA FINALE
% ══════════════════════════════════════════════════════════════════
fprintf('=============================================================\n');
fprintf('  RIEPILOGO STATISTICO\n');
fprintf('=============================================================\n');
fprintf('%-14s  %8s  %9s  %9s  %9s  %8s\n','Punto','t [s]','Tf_sim','Tf_real','Errore[K]','Tc_sim');
fprintf('%s\n', repmat('-',1,62));
CHK_t  = [240, 2040, 2940, 4740, 5640, 6599];
CHK_Tf = [24.08, 22.89, 26.41, NaN, NaN, NaN];
CHK_nm = {'SP1 inizio','SP1 fine','RIPO1 fine','SP2 fine','RIPO2 fine','Fine test'};
for j=1:numel(CHK_t)
    ki  = min(CHK_t(j)+1, N_STEP+1);
    tfs = Tf_s(ki);  tcs = Tc_s(ki);
    if ~isnan(CHK_Tf(j))
        fprintf('%-14s  %8d  %9.2f  %9.2f  %+9.2f  %8.2f\n', ...
            CHK_nm{j}, CHK_t(j), tfs, CHK_Tf(j), tfs-CHK_Tf(j), tcs);
    else
        fprintf('%-14s  %8d  %9.2f  %9s  %9s  %8.2f\n', ...
            CHK_nm{j}, CHK_t(j), tfs, 'n/a', 'n/a', tcs);
    end
end
fprintf('%s\n\n', repmat('-',1,62));

if has_real
    % MAPE per fase attiva — accumula errori E riferimenti per il totale
    fasi_a = {[240,2040],[2940,4740],[5640,6600]};
    nomi_a = {'SP1','SP2','SP3'};
    all_err=[]; all_ref=[];
    fprintf('%-8s  %8s  %8s  %8s\n','Fase','MAPE','RMSE[K]','Match%');
    fprintf('%s\n', repmat('-',1,38));
    for fi=1:3
        t0=fasi_a{fi}(1); t1=fasi_a{fi}(2);
        mask = t_r>=t0 & t_r<t1;
        if ~any(mask), continue; end
        Tf_sim_i = interp1(t_sim, Tf_s, t_r(mask), 'linear','extrap');
        err_i    = Tf_sim_i - Tf_r(mask);
        mape_i   = 100*mean(abs(err_i)./max(abs(Tf_r(mask)),0.01));
        rmse_i   = sqrt(mean(err_i.^2));
        all_err  = [all_err; err_i];
        all_ref  = [all_ref; Tf_r(mask)];
        fprintf('%-8s  %7.2f%%  %8.3f  %8.1f%%\n', nomi_a{fi}, mape_i, rmse_i, max(0,100-mape_i));
    end
    if ~isempty(all_err)
        mape_g  = 100*mean(abs(all_err)./max(abs(all_ref),0.01));
        rmse_g  = sqrt(mean(all_err.^2));
        fprintf('%s\n', repmat('-',1,38));
        fprintf('%-8s  %7.2f%%  %8.3f  %8.1f%%\n','TOTALE',mape_g,rmse_g,max(0,100-mape_g));
    end
end

fprintf('\nFile salvati:\n');
fprintf('  figures/fig_risultati_sim.png\n');
fprintf('  figures/fig_pid_confronto.png\n');
fprintf('  figures/Risultati_Sim_Finale.csv\n');
