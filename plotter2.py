import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation

# Grid and time setup
Nx, Ny = 100, 100
Lx, Ly = 1.0, 1.0
dx, dy = Lx / Nx, Ly / Ny
x = np.linspace(0, Lx, Nx+1)
y = np.linspace(0, Ly, Ny+1)
X, Y = np.meshgrid(x, y)

# Time setup
dt = 5e-5
Nt = 1000
steps_per_frame = 1
paused = False

# Initialization
def initialize_fields():
    psi = np.zeros_like(X)
    sources = [(0.3, 0.5), (0.7, 0.3), (0.6, 0.7)]
    for sx, sy in sources:
        psi += np.exp(-100.0 * ((X - sx)**2 + (Y - sy)**2))
    Gamma = np.zeros_like(psi)
    Gamma_cumulative = np.zeros_like(psi)
    cx, cy = 0.5, 0.5
    radius = 0.12
    wall = ((X - cx)**2 + (Y - cy)**2) < radius**2
    psi[wall] = 0
    Gamma[wall] = 0
    Gamma_cumulative[wall] = 0
    return psi, Gamma, Gamma_cumulative, wall

def absorbing_bc(arr):
    arr[0, :] = arr[1, :]
    arr[-1, :] = arr[-2, :]
    arr[:, 0] = arr[:, 1]
    arr[:, -1] = arr[:, -2]

def update_fields(psi, Gamma, Gamma_cumulative, alpha, mu, kappa, u0, c=1.0, goal_force=2.0):
    psi_new = psi.copy()
    Gamma_new = Gamma.copy()
    Gamma_cum = Gamma_cumulative.copy()
    dpsi_dx = (np.roll(psi, -1, axis=1) - np.roll(psi, 1, axis=1)) / (2 * dx)
    dpsi_dy = (np.roll(psi, -1, axis=0) - np.roll(psi, 1, axis=0)) / (2 * dy)
    d2psi_dx2 = (np.roll(psi, -1, axis=1) - 2*psi + np.roll(psi, 1, axis=1)) / dx**2
    d2psi_dy2 = (np.roll(psi, -1, axis=0) - 2*psi + np.roll(psi, 1, axis=0)) / dy**2
    convection_x = (u0 + kappa * Gamma) * dpsi_dx
    convection_y = (u0 + kappa * Gamma) * dpsi_dy
    laplacian = d2psi_dx2 + d2psi_dy2
    goal_positions = [(0.9, 0.1), (0.1, 0.9), (0.9, 0.9)]
    total_goal_convection_x = np.zeros_like(psi)
    total_goal_convection_y = np.zeros_like(psi)
    for gx, gy in goal_positions:
        dxg = gx - X
        dyg = gy - Y
        dist = np.sqrt(dxg**2 + dyg**2) + 1e-5
        dir_x = dxg / dist
        dir_y = dyg / dist
        pull = goal_force / dist**2
        total_goal_convection_x += pull * dir_x
        total_goal_convection_y += pull * dir_y
    psi_new += dt * (c * laplacian - convection_x - convection_y - Gamma * psi - total_goal_convection_x - total_goal_convection_y)
    grad_mag = np.sqrt(dpsi_dx**2 + dpsi_dy**2)
    Gamma_new += dt * (alpha * grad_mag - mu * Gamma)
    Gamma_cum += Gamma_new * dt
    absorbing_bc(psi_new)
    absorbing_bc(Gamma_new)
    return psi_new, Gamma_new, Gamma_cum, dpsi_dx, dpsi_dy

fig, ax = plt.subplots(2, 2, figsize=(10, 10))
plt.subplots_adjust(bottom=0.4)
psi_img_2d = ax[0][0].imshow(np.zeros((Ny+1, Nx+1)), cmap='viridis', origin='lower', extent=[0, Lx, 0, Ly])
Gamma_img_2d = ax[0][1].imshow(np.zeros((Ny+1, Nx+1)), cmap='hot', origin='lower', extent=[0, Lx, 0, Ly])
cbar = plt.colorbar(Gamma_img_2d, ax=ax[0][1], orientation='vertical')
cbar.set_label('Conductance Γ')
psi_img_1d = ax[1][0].plot(x, np.zeros_like(x))[0]
Gamma_img_1d = ax[1][1].plot(x, np.zeros_like(x))[0]
quiver = ax[0][0].quiver(
    X[::5, ::5], Y[::5, ::5],
    np.zeros_like(X[::5, ::5]), np.zeros_like(Y[::5, ::5]),
    color='white', scale=10, pivot='middle', cmap='cool', clim=[0, 0.5]
)
quiver_toggle_ax = plt.axes([0.32, 0.02, 0.1, 0.04])
quiver_toggle_button = Button(quiver_toggle_ax, 'Toggle Arrows')
narrow_field_visible = True
step_text = ax[0][0].text(0.02, 0.95, '', transform=ax[0][0].transAxes, fontsize=10, color='white', bbox=dict(facecolor='black', alpha=0.5))

ax[0][0].set_title('psi (2D) + flow')
ax[0][1].set_title('Gamma (2D)')
ax[1][0].set_title('psi (1D slice)')
ax[1][1].set_title('Gamma (1D slice)')

ax_time = plt.axes([0.25, 0.08, 0.65, 0.03])
ax_alpha = plt.axes([0.25, 0.28, 0.65, 0.03])
ax_mu    = plt.axes([0.25, 0.24, 0.65, 0.03])
ax_kappa = plt.axes([0.25, 0.20, 0.65, 0.03])
ax_u0    = plt.axes([0.25, 0.16, 0.65, 0.03])
ax_speed = plt.axes([0.25, 0.12, 0.65, 0.03])

s_alpha = Slider(ax_alpha, 'alpha', 0.0, 0.2, valinit=0.05)
s_mu    = Slider(ax_mu,    'mu',    0.0, 0.1, valinit=0.01)
s_kappa = Slider(ax_kappa, 'kappa', 0.0, 2.0, valinit=1.0)
s_u0    = Slider(ax_u0,    'u0',    0.0, 2.0, valinit=0.8)
s_speed = Slider(ax_speed, 'Speed', 1, 100, valinit=1, valstep=1)
s_time = Slider(ax_time, 'Step', 0, Nt-1, valinit=0, valstep=1)

reset_ax = plt.axes([0.1, 0.02, 0.1, 0.04])
pause_ax = plt.axes([0.21, 0.02, 0.1, 0.04])
cumulative_ax = plt.axes([0.85, 0.02, 0.1, 0.04])

reset_button = Button(reset_ax, 'Reset')
pause_button = Button(pause_ax, 'Pause')
cumulative_button = Button(cumulative_ax, 'Show Γⁱⁿᵗ')
cumulative_button.tooltip = "Toggle between current Gamma and cumulative Gamma"
Gamma_img_2d.set_clim(0, 1.0)

min_ax = plt.axes([0.45, 0.02, 0.1, 0.04])
balanced_ax = plt.axes([0.67, 0.02, 0.1, 0.04])
max_ax = plt.axes([0.56, 0.02, 0.1, 0.04])
min_button = Button(min_ax, 'Min Params')
balanced_button = Button(balanced_ax, 'Balanced')
min_ax.set_title("No learning / drift")
max_ax.set_title("Fast growth + drift")
balanced_ax.set_title("Moderate dynamics")
max_button = Button(max_ax, 'Max Params')

psi, Gamma, Gamma_cumulative, wall = initialize_fields()
show_cumulative = False
cumulative_button.label.set_text('Show Γⁱⁿᵗ')

for gx, gy in [(0.9, 0.1), (0.1, 0.9), (0.9, 0.9)]:
    ax[0][0].scatter(gx, gy, color='cyan', s=100, marker='*')
ax[0][0].legend(['Goal(s)'], loc='upper right')

def set_params(alpha, mu, kappa, u0):
    s_alpha.set_val(alpha)
    s_mu.set_val(mu)
    s_kappa.set_val(kappa)
    s_u0.set_val(u0)

frame_index = 0
recorded_frames = []

def animate(frame):
    global psi, Gamma, Gamma_cumulative, wall, steps_per_frame, paused, show_cumulative
    if paused:
        return
    alpha = s_alpha.val
    mu = s_mu.val
    kappa = s_kappa.val
    u0 = s_u0.val
    steps_per_frame = int(s_speed.val)
    for _ in range(steps_per_frame):
        recorded_frames.append((psi.copy(), Gamma.copy(), Gamma_cumulative.copy()))
        psi, Gamma, Gamma_cumulative, dpsi_dx, dpsi_dy = update_fields(psi, Gamma, Gamma_cumulative, alpha, mu, kappa, u0)
    masked_psi = np.ma.masked_where(wall, psi)
    psi_img_2d.set_data(masked_psi)
    if show_cumulative:
        Gamma_img_2d.set_data(np.ma.masked_where(wall, Gamma_cumulative))
    else:
        Gamma_img_2d.set_data(np.ma.masked_where(wall, Gamma))
    psi_img_1d.set_ydata(psi[Ny//2, :])
    Gamma_img_1d.set_ydata(Gamma[Ny//2, :])
    mag = np.sqrt(dpsi_dx**2 + dpsi_dy**2)
    quiver.set_UVC(dpsi_dx[::5, ::5], dpsi_dy[::5, ::5], mag[::5, ::5])
    step_text.set_text(f"Step: {len(recorded_frames)}")
    quiver.set_visible(narrow_field_visible)
    return psi_img_2d, Gamma_img_2d, psi_img_1d, Gamma_img_1d, quiver

def reset(event):
    global psi, Gamma, Gamma_cumulative, wall
    psi, Gamma, Gamma_cumulative, wall = initialize_fields()

def toggle_pause(event):
    global paused
    paused = not paused
    pause_button.label.set_text('Resume' if paused else 'Pause')

def toggle_cumulative(event):
    global show_cumulative
    show_cumulative = not show_cumulative
    if show_cumulative:
        cumulative_button.label.set_text('Show Γ')
        Gamma_img_2d.set_clim(0, np.max(Gamma_cumulative))
    else:
        cumulative_button.label.set_text('Show Γⁱⁿᵗ')
        Gamma_img_2d.set_clim(0, 1.0)

reset_button.on_clicked(reset)
pause_button.on_clicked(toggle_pause)
cumulative_button.on_clicked(toggle_cumulative)
min_button.on_clicked(lambda e: set_params(0.0, 0.0, 0.0, 0.0))
max_button.on_clicked(lambda e: set_params(0.2, 0.0, 2.0, 2.0))
balanced_button.on_clicked(lambda e: set_params(0.05, 0.01, 1.0, 0.5))

ani = FuncAnimation(fig, animate, interval=1000)

def on_time_slider(val):
    global psi, Gamma, Gamma_cumulative
    idx = int(val)
    if idx < len(recorded_frames):
        psi, Gamma, Gamma_cumulative = recorded_frames[idx]
        masked_psi = np.ma.masked_where(wall, psi)
        psi_img_2d.set_data(masked_psi)
        if show_cumulative:
            Gamma_img_2d.set_data(np.ma.masked_where(wall, Gamma_cumulative))
        else:
            Gamma_img_2d.set_data(np.ma.masked_where(wall, Gamma))
        psi_img_1d.set_ydata(psi[Ny//2, :])
        Gamma_img_1d.set_ydata(Gamma[Ny//2, :])
        fig.canvas.draw_idle()

def toggle_quiver(event):
    global narrow_field_visible
    narrow_field_visible = not narrow_field_visible
    quiver.set_visible(narrow_field_visible)
    fig.canvas.draw_idle()

quiver_toggle_button.on_clicked(toggle_quiver)
s_time.on_changed(on_time_slider)
plt.show()