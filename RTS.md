\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{siunitx}
\usepackage{hyperref}
\hypersetup{colorlinks=true, urlcolor=blue}
\setlength{\parskip}{4pt}
\setlength{\parindent}{0pt}

\begin{document}

{\Large \textbf{ARP Experimental Prereg \& How-To (One Page)}}\\
\textbf{Version:} v1.0 \quad
\textbf{Contact:} RDM3DC (DM on X) \quad
\textbf{License:} CC-BY 4.0

\hrule
\vspace{0.6em}

\textbf{Goal.} Provide two decisive, falsifiable tests of the ARP framework:
(1) \textbf{Hydride Tc(P) ridge} (LaH\textsubscript{10} in a DAC), and
(2) \textbf{Bell-chip geometry/bath} test (non-signaling) showing the predicted visibility and distance laws.

\textbf{Core model (minimal).}
\[
\xi=\sqrt{D/\mu},\qquad
W(L,\xi)=\frac{e^{-L/\xi}}{L},\qquad
\alpha_{\text{geom}}\propto \mu\,W(L,\xi).
\]
A polaritonic (or phonon-) channel contributes an effective detuning term
\[
\Delta_{\text{eff}}=k\,\bigg(\frac{g}{\omega}\bigg)^2 \times Q_{\text{fac}}\times \mathcal{C}^2,\quad
\lambda_{\text{tot}}=\lambda_0+\lambda(\alpha_{\text{geom}},\Delta_{\text{eff}}).
\]
Critical temperature via Allen–Dynes:
\[
T_c=\frac{\omega_{\log}}{1.2}\exp\!\left[-\frac{1.04(1+\lambda_{\text{tot}})}{\lambda_{\text{tot}}-\mu^\*(1+0.62\lambda_{\text{tot}})}\right].
\]

% =====================================================
\section*{Experiment A: Hydrides (LaH\textsubscript{10}) Ridge Test}

\textbf{Objective.} Map $T_c(P)$ from \SI{120}{–}\SI{220}{GPa}; compare to ARP ridge and derivative falsifiers.

\textbf{Vary.} Pressure $P$; (optional) mode-mix or coupling proxy $g$.\\
\textbf{Measure.} 4-probe $R(T)$, magnetization/Meissner $\chi(T)$ if available; extracted $T_c(P)$ (onset and zero-$R$).
Optional: $\omega_{\log}(P)$ from phonons; $\mu^\*(P)$.

\textbf{Predictions / falsifiers (examples).}
\begin{itemize}
\item \emph{Ridge \& sign flip:} $dT_c/dP \sim +1$~K/GPa near \SI{150}{–}\SI{170}{GPa}, then $\sim -0.4$~K/GPa beyond $\sim$\SI{200}{GPa}.
\item \emph{300~K feasibility window:} Contour emerges in $\sim$\SI{160}{–}\SI{200}{GPa} if $\Delta_{\text{eff}}$ or $g$ is sufficient for given $\omega_{\log}$.
\item \emph{Fail criteria:} No ridge/derivative trends beyond thermal/heating artifacts; maps cannot be reconciled by any reasonable $(g,\omega_{\log},\mu^\*)$.
\end{itemize}

\textbf{CSV schema (minimal).}
\begin{verbatim}
# hydride experiment
Pressure_GPa, Tc_K
120, 191
136, 241
... ...
# optional DFT curves
Pressure_GPa, g_eV, omega_log_K, mu_star
150, 0.30, 1230, 0.10
... ...
\end{verbatim}

\textbf{Quick analysis (local).}
\begin{verbatim}
python arp_fit_overlay.py --mode hydride \
  --exp_csv your_LaH10_TcP.csv \
  --dft_csv your_LaH10_DFT.csv \
  --outdir fit_out_hydride
# Produces: hydride_fit_overlay.png + hydride_fit_report.json
\end{verbatim}

\textbf{What to attach in a report.} The $T_c(P)$ overlay (exp vs ARP baseline and ARP+Δ),
the $g_{\text{required}}(P)$ or $\Delta_{\text{req}}(P)$ curve to reach 300~K, and the derivative plot
$dT_c/dP$ showing the ridge peak/flip.

\emph{Safety.} Standard DAC high-pressure safety protocols (shielding, gasket integrity, calibrated force, ruby fluorescence, etc.).

% =====================================================
\section*{Experiment B: Bell-Chip (Geometry/Bath) Non-Signaling Test}

\textbf{Objective.} Verify the ARP geometry law and bath sensitivity without signaling.

\textbf{Vary.} Emitter/detector \textbf{separation} $L$ (hundreds~$\mu$m to cm), controlled bath parameter $\mu$ (thermal/phononic noise), optional photonic/phononic detuning.

\textbf{Measure.} Bell-inequality visibility $V$ vs $\mu$ at fixed $L$; $V$ vs $L$ at fixed $\mu$.

\textbf{Predictions / falsifiers.}
\begin{itemize}
\item \emph{Distance law:} Effective coupling scales with $\alpha(L)\propto e^{-L/\xi}/L$; visibility families collapse accordingly.
\item \emph{Bath law:} $V(\mu)$ exhibits a characteristic knee/roll-off (from telegrapher-type relaxation); stronger $\mu$ lowers $V$.
\item \emph{Non-signaling preserved:} No superluminal information transfer; correlations adjust via hidden channel equilibration.
\item \emph{Fail criteria:} No $L$-law; no $V(\mu)$ drop; or violations of non-signaling.
\end{itemize}

\textbf{CSV schema (minimal).}
\begin{verbatim}
# visibility vs bath at fixed L
L_mm, mu_units, Visibility
10.0, 0.00, 0.92
10.0, 0.05, 0.81
... ...
# visibility vs distance at fixed mu
L_mm, Visibility
1.0, 0.95
5.0, 0.88
... ...
\end{verbatim}

\textbf{Analysis outline.} Fit $V(L)$ to $A\,e^{-L/\xi}/L + B$; fit $V(\mu)$ to the predicted
relaxation family (we provide scripts to generate overlays and extract $\xi$).

% =====================================================
\section*{Outputs to Generate (Both Tracks)}

\textbf{Hydrides:}
\begin{itemize}
\item $T_c(P)$ overlay (experiment vs ARP baseline and ARP+$\Delta_{\text{eff}}$).
\item Feasibility maps: $T_c$ vs $(P,\Delta)$ or $(P,g)$; $g_{\text{required}}(P)$ for $T_c=$~300~K.
\item Derivative falsifiers: $dT_c/dP$ at fixed $\Delta$, $dT_c/d\Delta$ at fixed $P$.
\end{itemize}

\textbf{Bell-chip:}
\begin{itemize}
\item $V$ vs $L$ with fit to $e^{-L/\xi}/L$; extracted $\xi$ and uncertainty.
\item $V$ vs $\mu$ families; location of the knee; collapse across $L$ when rescaled by $\alpha(L)$.
\end{itemize}

% =====================================================
\section*{Minimal Repro (No Proprietary Data)}

We provide reference scripts:
\begin{itemize}
\item \texttt{arp\_fit\_overlay.py} --- fits $\{s_\lambda, k\}$ to your hydride dome and produces overlays (PNG) + JSON report.
\item Templates: \texttt{TEMPLATE\_hydride\_film\_inputs.csv}, \texttt{TEMPLATE\_squid\_film\_inputs.csv}.
\end{itemize}
Drop your CSVs, run the commands above, and attach:
(1) overlay PNGs, (2) falsifier plots, (3) the JSON fit report (RMSE, best-fit params).

% =====================================================
\section*{Pass/Fail Criteria (Preregistered)}

\textbf{Hydrides (pass if all true):}
\begin{enumerate}
\item $T_c(P)$ exhibits a ridge consistent with ARP maps \emph{and} the measured $dT_c/dP$ shows the predicted sign/magnitude near the window.
\item For plausible $(g,\omega_{\log},\mu^\*)$, the observed dome overlays within uncertainty bands; otherwise \emph{fail}.
\end{enumerate}

\textbf{Bell-chip (pass if all true):}
\begin{enumerate}
\item $V(L)$ fits $e^{-L/\xi}/L$ with finite $\xi$ and sensible residuals.
\item $V(\mu)$ decreases with the predicted knee/shape; non-signaling holds. Absence of either trend \emph{fails} ARP.
\end{enumerate}

\vspace{0.3em}
\hrule
\vspace{0.3em}

\textbf{FAQ.}
\emph{Does ARP violate relativity?} No. The hidden channel is a non-signaling equilibrator; Bell correlations appear as geometry/bath constraints, not superluminal messaging.\\
\emph{What about ``RTS'' claims?} Only after zero-$R$ \emph{and} Meissner at the stated $T$, with controls and replication.

\textbf{Acknowledgements.} Thanks to groups suggesting LaH\textsubscript{10} DAC runs and Bell-chip tests; we will credit collaborators in the repo.

\end{document}
