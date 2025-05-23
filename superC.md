import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Simulation parameters
N = 10                             # number of inductive segments in the chain
L0 = 0.1                           # base inductance of each segment (Henry)
# Critical current for each segment (in Amps)
thresholds = np.full(N, 1.5)       # default all 1.5 A
thresholds[N//2] = 1.0            # example: make the middle segment weaker (1.0 A)
R_quench_value = 10.0              # resistance (Ohm) of a segment after quench
V_supply = 5.0                     # supply voltage (Volts) applied to the series chain
dt = 0.001                         # time step for simulation (seconds)
t_total = 0.5                      # total simulation time (seconds)

# Arrays to record time and current
time = np.arange(0, t_total + dt, dt)
current = np.zeros_like(time)

# State tracking for segments
quenched = np.zeros(N, dtype=bool)       # boolean flags for whether each segment has quenched
t_quench = np.full(N, np.inf)           # time each segment quenched (inf if not quenched)

# Initial condition
I = 0.0  # current (A)
current[0] = I

# Time-stepped simulation of the circuit
for k in range(1, len(time)):
    t = time[k]
    # Determine inductance and resistance of each segment based on current and state
    L_vals = np.full(N, L0)    # start with base inductances
    R_vals = np.zeros(N)       # start with zero resistances (superconducting)
    for i in range(N):
        if quenched[i]:
            # Segment already quenched: use resistive state
            L_vals[i] = L0            # (keeping inductance constant for simplicity)
            R_vals[i] = R_quench_value
        else:
            # Superconducting state
            if I >= thresholds[i]:
                # Quench triggered for this segment
                quenched[i] = True
                t_quench[i] = t
                R_vals[i] = R_quench_value
                L_vals[i] = L0        # inductance remains (could also keep it at increased value)
            else:
                R_vals[i] = 0.0
                # Adaptive inductance: increase inductance as current approaches critical
                if I >= 0.9 * thresholds[i]:
                    L_vals[i] = 5 * L0  # e.g., 5x inductance when above 90% of I_c
                else:
                    L_vals[i] = L0
    # Calculate total L and R for series circuit
    L_total = L_vals.sum()
    R_total = R_vals.sum()
    # Update current using V = L_total * dI/dt + I*R_total
    dI_dt = (V_supply - I * R_total) / L_total  # current derivative
    I = I + dI_dt * dt
    current[k] = I

# Set up the plot for animation
fig, (ax_chain, ax_current) = plt.subplots(1, 2, figsize=(10, 4))
fig.suptitle("Adaptive Impedance Network Simulation", fontsize=14)

# Left plot: 1D chain visualization
ax_chain.set_title("Current along 1D Superconducting Chain")
ax_chain.set_xlim(0, N)
ax_chain.set_ylim(-0.5, 0.5)
ax_chain.set_xlabel("Segment Position")
ax_chain.get_yaxis().set_visible(False)  # hide y-axis
# Draw static base line for each segment
for i in range(N):
    ax_chain.plot([i, i+1], [0, 0], color='gray', linewidth=2, alpha=0.5)
# Initialize arrows (quiver) for current (start with no current)
X = np.arange(0, N, 1)                 # arrow starting positions (each segment start)
Y = np.zeros(N)
U = np.zeros(N)                       # arrow lengths (initially 0)
V = np.zeros(N)
colors = ['blue'] * N                 # initial colors (all superconducting)
quiver = ax_chain.quiver(X, Y, U, V, color=colors, scale_units='xy', scale=1, width=0.005)

# Right plot: Current vs time
ax_current.set_title("Circuit Current vs Time")
ax_current.set_xlabel("Time (s)")
ax_current.set_ylabel("Current (A)")
# Plot critical current level for reference (using minimum I_c in the system)
I_c_min = thresholds.min()
ax_current.axhline(y=I_c_min, color='red', linestyle='--', label='Critical current')
# Initialize the current vs time line
line_current, = ax_current.plot([], [], color='blue', label='Current')
ax_current.set_xlim(0, t_total)
ax_current.set_ylim(0, 1.2 * max(current.max(), I_c_min))
ax_current.legend(loc='upper right')

# Animation update function
def update(frame_index):
    # This function updates the arrows and graph to the state at `frame_index`
    t = time[frame_index]
    I_val = current[frame_index]
    # Update arrows for all segments:
    # Arrow length scaled to current/critical (cap the length to 0.95 of segment for visibility)
    if I_c_min > 0:
        frac = abs(I_val) / I_c_min
    else:
        frac = 0.0
    arrow_length = min(frac, 0.95)     # ensure arrow not too long
    U_vals = np.ones(N) * arrow_length * (1 if I_val >= 0 else -1)
    V_vals = np.zeros(N)
    # Set arrow colors based on which segments have quenched by this time
    for i in range(N):
        if t_quench[i] != np.inf and t >= t_quench[i]:
            colors[i] = 'red'    # segment i has quenched (or is quenching now)
        else:
            colors[i] = 'blue'
    # Apply updates to the Quiver object and line plot
    quiver.set_UVC(U_vals, V_vals)
    quiver.set_color(colors)
    line_current.set_data(time[:frame_index+1], current[:frame_index+1])
    return quiver, line_current

# Create and display the animation
frame_indices = np.arange(0, len(time), 2)  # use every 2nd time-step for smoother animation
ani = FuncAnimation(fig, update, frames=frame_indices, interval=20, blit=True)
plt.tight_layout()
plt.show()
