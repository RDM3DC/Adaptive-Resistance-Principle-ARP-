import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML

class DynamicResistanceSimulator:
    def __init__(self, alpha=1.0, mu=0.5, G0=0.0, t_max=10.0, dt=0.01):
        """
        Initialize the simulator for the Dynamic Resistance Law.
        
        Parameters:
        -----------
        alpha : float
            Scaling factor for the input magnitude.
        mu : float
            Resistance coefficient.
        G0 : float
            Initial value of G.
        t_max : float
            Maximum simulation time.
        dt : float
            Time step for simulation.
        """
        self.alpha = alpha
        self.mu = mu
        self.G0 = G0
        self.dt = dt
        self.t_max = t_max
        
        # Create time array
        self.t = np.arange(0, t_max, dt)
        self.n_steps = len(self.t)
        
        # Initialize arrays
        self.G = np.zeros(self.n_steps)
        self.G[0] = G0
        self.I = np.zeros(self.n_steps)
        
    def set_constant_input(self, I0):
        """Set a constant input signal."""
        self.I = np.ones(self.n_steps) * I0
        
    def set_step_input(self, I0, step_time):
        """Set a step input signal."""
        self.I = np.zeros(self.n_steps)
        step_idx = int(step_time / self.dt)
        self.I[step_idx:] = I0
        
    def set_pulse_input(self, I0, start_time, duration):
        """Set a pulse input signal."""
        self.I = np.zeros(self.n_steps)
        start_idx = int(start_time / self.dt)
        end_idx = int((start_time + duration) / self.dt)
        self.I[start_idx:end_idx] = I0
        
    def set_sine_input(self, amplitude, frequency, phase=0):
        """Set a sinusoidal input signal."""
        self.I = amplitude * np.abs(np.sin(2 * np.pi * frequency * self.t + phase))
        
    def set_exponential_input(self, I0, k):
        """Set an exponentially changing input signal."""
        self.I = I0 * np.exp(k * self.t)
        
    def set_linear_input(self, I0, slope):
        """Set a linearly changing input signal."""
        self.I = I0 + slope * self.t
        
    def simulate(self):
        """Run the simulation using the difference equation."""
        for i in range(1, self.n_steps):
            # Update G using the difference equation form of the Dynamic Resistance Law
            self.G[i] = self.G[i-1] + self.dt * (self.alpha * np.abs(self.I[i-1]) - self.mu * self.G[i-1])
            
    def analytical_solution(self, input_type):
        """Calculate the analytical solution for specific input types."""
        analytical_G = np.zeros(self.n_steps)
        
        if input_type == "constant":
            I0 = self.I[0]
            for i, t_val in enumerate(self.t):
                analytical_G[i] = (self.alpha * I0 / self.mu) * (1 - np.exp(-self.mu * t_val)) + self.G0 * np.exp(-self.mu * t_val)
                
        elif input_type == "exponential":
            I0 = self.I[0]
            k = np.log(self.I[-1] / I0) / self.t_max
            for i, t_val in enumerate(self.t):
                if np.abs(self.mu + k) < 1e-10:  # Check for near-zero denominator
                    analytical_G[i] = self.alpha * I0 * t_val * np.exp(k * t_val) + self.G0 * np.exp(-self.mu * t_val)
                else:
                    analytical_G[i] = (self.alpha * I0 / (self.mu + k)) * (np.exp(k * t_val) - np.exp(-self.mu * t_val)) + self.G0 * np.exp(-self.mu * t_val)
        
        return analytical_G
        
    def plot_results(self, title=None, analytical=None):
        """Plot the simulation results."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # Plot input
        ax1.plot(self.t, self.I, 'r-', label='Input |I(t)|')
        ax1.set_ylabel('Input Magnitude')
        ax1.set_title('Input Signal' if title is None else f'{title} - Input')
        ax1.grid(True)
        ax1.legend()
        
        # Plot response
        ax2.plot(self.t, self.G, 'b-', label='Simulated G(t)')
        
        if analytical is not None:
            analytical_G = self.analytical_solution(analytical)
            ax2.plot(self.t, analytical_G, 'g--', label='Analytical G(t)')
            
        ax2.set_xlabel('Time')
        ax2.set_ylabel('System Response')
        ax2.set_title('System Response According to the Dynamic Resistance Law')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        return fig
        
    def animate_response(self, analytical=None):
        """Create an animation of the system response."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # Set up the axes
        ax1.set_ylabel('Input Magnitude')
        ax1.set_title('Input Signal')
        ax1.grid(True)
        
        ax2.set_xlabel('Time')
        ax2.set_ylabel('System Response')
        ax2.set_title('System Response (Dynamic Resistance Law)')
        ax2.grid(True)
        
        # Set x limits
        ax1.set_xlim(0, self.t_max)
        ax2.set_xlim(0, self.t_max)
        
        # Set y limits with some padding
        ax1.set_ylim(0, max(self.I) * 1.1)
        ax2.set_ylim(0, max(self.G) * 1.1)
        
        # Initialize empty lines
        line_input, = ax1.plot([], [], 'r-', label='Input |I(t)|')
        line_response, = ax2.plot([], [], 'b-', label='G(t)')
        
        if analytical is not None:
            analytical_G = self.analytical_solution(analytical)
            line_analytical, = ax2.plot([], [], 'g--', label='Analytical G(t)')
        
        ax1.legend()
        ax2.legend()
        
        def init():
            line_input.set_data([], [])
            line_response.set_data([], [])
            if analytical is not None:
                line_analytical.set_data([], [])
                return line_input, line_response, line_analytical
            return line_input, line_response
        
        def update(frame):
            frame = int(frame)
            line_input.set_data(self.t[:frame], self.I[:frame])
            line_response.set_data(self.t[:frame], self.G[:frame])
            if analytical is not None:
                line_analytical.set_data(self.t[:frame], analytical_G[:frame])
                return line_input, line_response, line_analytical
            return line_input, line_response
        
        frames = np.linspace(0, self.n_steps, 100).astype(int)
        anim = FuncAnimation(fig, update, frames=frames, init_func=init, blit=True)
        plt.close()  # Prevent display of the static plot
        
        return anim
        
    def parameter_sweep(self, mu_values):
        """Perform a parameter sweep for different values of mu."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        original_mu = self.mu
        original_G = self.G.copy()
        
        for mu in mu_values:
            self.mu = mu
            self.G = np.zeros(self.n_steps)
            self.G[0] = self.G0
            self.simulate()
            ax.plot(self.t, self.G, label=f'μ = {mu}')
            
        # Restore original values
        self.mu = original_mu
        self.G = original_G
        
        ax.set_xlabel('Time')
        ax.set_ylabel('System Response G(t)')
        ax.set_title('Effect of Resistance Parameter μ on System Response')
        ax.grid(True)
        ax.legend()
        
        return fig

    def compare_inputs(self):
        """Compare system responses to different input types."""
        # Store original input
        original_I = self.I.copy()
        original_G = self.G.copy()
        
        # Create different inputs
        self.set_constant_input(1.0)
        self.G = np.zeros(self.n_steps)
        self.G[0] = self.G0
        self.simulate()
        G_constant = self.G.copy()
        
        self.set_step_input(1.0, self.t_max/5)
        self.G = np.zeros(self.n_steps)
        self.G[0] = self.G0
        self.simulate()
        G_step = self.G.copy()
        
        self.set_sine_input(1.0, 0.5)
        self.G = np.zeros(self.n_steps)
        self.G[0] = self.G0
        self.simulate()
        G_sine = self.G.copy()
        
        self.set_exponential_input(0.1, 0.3)
        self.G = np.zeros(self.n_steps)
        self.G[0] = self.G0
        self.simulate()
        G_exp = self.G.copy()
        
        # Plot results
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Inputs
        ax1.plot(self.t, original_I, 'k:', label='Original')
        ax1.plot(self.t, np.ones(self.n_steps), 'r-', label='Constant')
        step_input = np.zeros(self.n_steps)
        step_input[int(self.t_max/5 / self.dt):] = 1.0
        ax1.plot(self.t, step_input, 'g-', label='Step')
        ax1.plot(self.t, np.sin(2 * np.pi * 0.5 * self.t), 'b-', label='Sine')
        ax1.plot(self.t, 0.1 * np.exp(0.3 * self.t), 'm-', label='Exponential')
        
        ax1.set_ylabel('Input Magnitude')
        ax1.set_title('Different Input Signals')
        ax1.grid(True)
        ax1.legend()
        
        # Responses
        ax2.plot(self.t, original_G, 'k:', label='Original Response')
        ax2.plot(self.t, G_constant, 'r-', label='Constant Response')
        ax2.plot(self.t, G_step, 'g-', label='Step Response')
        ax2.plot(self.t, G_sine, 'b-', label='Sine Response')
        ax2.plot(self.t, G_exp, 'm-', label='Exponential Response')
        
        ax2.set_xlabel('Time')
        ax2.set_ylabel('System Response')
        ax2.set_title('System Responses to Different Inputs')
        ax2.grid(True)
        ax2.legend()
        
        # Restore original values
        self.I = original_I
        self.G = original_G
        
        plt.tight_layout()
        return fig

# Example usage
if __name__ == "__main__":
    # Create simulator
    sim = DynamicResistanceSimulator(alpha=1.0, mu=0.5, G0=0, t_max=20.0)
    
    # Test with constant input
    sim.set_constant_input(1.0)
    sim.simulate()
    fig1 = sim.plot_results(title="Constant Input", analytical="constant")
    
    # Test with step input
    sim.set_step_input(1.0, 5.0)
    sim.simulate()
    fig2 = sim.plot_results(title="Step Input")
    
    # Test with sine input
    sim.set_sine_input(1.0, 0.2)
    sim.simulate()
    fig3 = sim.plot_results(title="Sinusoidal Input")
    
    # Test with exponential input
    sim.set_exponential_input(0.1, 0.2)
    sim.simulate()
    fig4 = sim.plot_results(title="Exponential Input", analytical="exponential")
    
    # Parameter sweep
    fig5 = sim.parameter_sweep([0.1, 0.3, 0.5, 1.0, 2.0])
    
    # Compare different inputs
    fig6 = sim.compare_inputs()
    
    # Show all figures
    plt.show()
    
    # Create animation
    sim.set_step_input(1.0, 5.0)
    sim.simulate()
    anim = sim.animate_response()
    HTML(anim.to_jshtml())

# Function to demonstrate key properties of the Dynamic Resistance Law
def demonstrate_dynamic_law_properties():
    """Demonstrate key properties of the Dynamic Resistance Law."""
    plt.figure(figsize=(15, 12))
    
    # Property 1: Response lag
    # Show how the system response lags behind input changes
    plt.subplot(2, 2, 1)
    sim = DynamicResistanceSimulator(alpha=1.0, mu=0.5, t_max=15.0)
    sim.set_step_input(1.0, 5.0)
    sim.simulate()
    plt.plot(sim.t, sim.I, 'r-', label='Input')
    plt.plot(sim.t, sim.G, 'b-', label='Response')
    plt.axvline(x=5.0, color='gray', linestyle='--')
    plt.title("Property 1: Response Lag")
    plt.xlabel("Time")
    plt.ylabel("Magnitude")
    plt.legend()
    plt.grid(True)
    
    # Property 2: Resistance proportional to change rate
    # Show how faster changes encounter more resistance
    plt.subplot(2, 2, 2)
    sim1 = DynamicResistanceSimulator(alpha=1.0, mu=0.5, t_max=15.0)
    sim1.set_linear_input(0, 0.1)  # Slow change
    sim1.simulate()
    
    sim2 = DynamicResistanceSimulator(alpha=1.0, mu=0.5, t_max=15.0)
    sim2.set_linear_input(0, 0.3)  # Fast change
    sim2.simulate()
    
    # Calculate instantaneous resistance
    resistance1 = sim1.mu * sim1.G
    resistance2 = sim2.mu * sim2.G
    
    plt.plot(sim1.t, resistance1, 'g-', label='Resistance (slow change)')
    plt.plot(sim2.t, resistance2, 'r-', label='Resistance (fast change)')
    plt.title("Property 2: Resistance Proportional to Rate of Change")
    plt.xlabel("Time")
    plt.ylabel("Resistance Force")
    plt.legend()
    plt.grid(True)
    
    # Property 3: Equilibrium state
    # Show how system reaches equilibrium when input is constant
    plt.subplot(2, 2, 3)
    sim = DynamicResistanceSimulator(alpha=1.0, mu=0.5, t_max=15.0)
    sim.set_constant_input(1.0)
    sim.simulate()
    
    # Calculate driving force and resistance
    driving_force = sim.alpha * sim.I
    resistance = sim.mu * sim.G
    
    plt.plot(sim.t, driving_force, 'r-', label='Driving Force')
    plt.plot(sim.t, resistance, 'b-', label='Resistance')
    plt.axhline(y=sim.alpha/sim.mu, color='gray', linestyle='--', label='Equilibrium')
    plt.title("Property 3: Equilibrium State")
    plt.xlabel("Time")
    plt.ylabel("Force")
    plt.legend()
    plt.grid(True)
    
    # Property 4: Resistance coefficient effect
    # Show how different μ values affect adaptation speed
    plt.subplot(2, 2, 4)
    mu_values = [0.2, 0.5, 1.0]
    for mu in mu_values:
        sim = DynamicResistanceSimulator(alpha=1.0, mu=mu, t_max=15.0)
        sim.set_step_input(1.0, 2.0)
        sim.simulate()
        plt.plot(sim.t, sim.G, label=f'μ = {mu}')
    
    plt.axvline(x=2.0, color='gray', linestyle='--')
    plt.title("Property 4: Effect of Resistance Coefficient")
    plt.xlabel("Time")
    plt.ylabel("Response")
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    return plt.gcf()

# Run the demonstration
demonstrate_dynamic_law_properties()
