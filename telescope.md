import numpy as np
import matplotlib.pyplot as plt

# ------------------------
# 1) Simulation Parameters
# ------------------------
N = 5                # total number of nodes (0 .. N-1)
C = 1e-6             # each node's capacitance to ground (F)
alpha = 1e-4         # growth rate for G
mu    = 1e-4         # decay rate for G
dt    = 1e-5         # time step for integration (s)
tmax  = 0.01         # total simulation time (s)
drive_freq = 1e3     # driving signal frequency (Hz)
drive_amp  = 1.0     # driving amplitude (volts)

# We'll have N-1 conductors: G0..G(N-2)
# G_i(t) connects node i to node i+1
# boundary nodes: node0=driven, node(N-1)=ground

# ------------------------
# 2) Initialize Arrays
# ------------------------
ntsteps = int(tmax / dt)
time    = np.linspace(0, tmax, ntsteps)

# node voltages: index 0..N-1
# node 0 => driven, node N-1 => ground
V = np.zeros(N, dtype=float)

# conduction array G: index 0..N-1
# G_i is the conductance between node i and i+1
G = np.ones(N-1, dtype=float) * 1e-3   # initial small conductances

# We'll record data for analysis
V_history = np.zeros((ntsteps, N))
G_history = np.zeros((ntsteps, N-1))

# ------------------------
# 3) Helper Functions
# ------------------------

def drive_voltage(t):
    """ Time-varying drive at node 0. E.g., sinusoid. """
    return drive_amp * np.sin(2.0 * np.pi * drive_freq * t)

def compute_currents(V, G):
    """
    Compute currents I_i from node i to node i+1 
    based on the current conductances G_i and node voltages V.
    I_i = G_i * (V[i] - V[i+1]).
    We'll return an array I of length N-1.
    """
    I = np.zeros(N-1, dtype=float)
    for i in range(N-1):
        I[i] = G[i] * (V[i] - V[i+1])
    return I

# ------------------------
# 4) Main Loop
# ------------------------
for step in range(ntsteps):
    t = step * dt

    # 4.1) Set boundary voltages
    V[0]      = drive_voltage(t)   # node 0 driven by sinusoid
    V[N-1]    = 0.0                # node N-1 is ground

    # 4.2) Compute currents (based on old V,G)
    I = compute_currents(V, G)

    # 4.3) Update internal node voltages:
    # Each node i (1 .. N-2) has:
    #   C dV_i/dt = sum of currents from neighbors
    #   i.e. from (i-1->i) and from (i->i+1)
    # We'll do a simple Euler step for dV_i/dt.
    dV = np.zeros(N, dtype=float)
    for i in range(1, N-1):
        I_in  = G[i-1]*(V[i-1] - V[i])  # current from node (i-1) to i
        I_out = 0.0
        if i < N-1:
            I_out = G[i]*(V[i] - V[i+1])
        net_current = I_in - I_out
        dV[i] = (net_current) / C   # dV/dt = I/C

    # Euler update for internal nodes
    for i in range(1, N-1):
        V[i] += dt * dV[i]

    # 4.4) Update G using ARP-like rule:
    # dG_i/dt = alpha * |I_i| - mu * G_i
    for i in range(N-1):
        dGdt = alpha * abs(I[i]) - mu * G[i]
        G[i] += dt * dGdt
        if G[i] < 0.0:
            G[i] = 0.0  # clamp to non-negative

    # 4.5) Record data
    V_history[step,:] = V[:]
    G_history[step,:] = G[:]

# ------------------------
# 5) Print final results
# ------------------------
print("Final G:", G)
print("Final node V:", V)

# Optionally, plot results
plt.figure(figsize=(10,5))

# Plot the conductances over time
plt.subplot(1,2,1)
for i in range(N-1):
    plt.plot(time, G_history[:,i], label=f"G{i}")
plt.xlabel("Time (s)")
plt.ylabel("Conductance (S)")
plt.title("Adaptive Conductances")
plt.legend()

# Plot node voltages
plt.subplot(1,2,2)
for i in range(N):
    plt.plot(time, V_history[:,i], label=f"V{i}")
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.title("Node Voltages")
plt.legend()

plt.tight_layout()
plt.show()
