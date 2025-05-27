import torch

class ARP_Optimiser(torch.optim.Optimizer):
    r"""
    ARP_Optimiser implements a simple version of the conduction-like update:
        G_{t+1} = (1 - mu) * G_t + alpha * |grad|
        p_{t+1} = p_t - lr * G_{t+1} * sign(grad)

    Where:
      - alpha, mu are conduction-like parameters
      - lr is the parameter step size for actual weight updates
      - G is an internal state tracking conduction magnitude

    Args:
        params (iterable): iterable of parameters to optimize
        lr (float): step size applied to the update (default: 1e-3)
        alpha (float): conduction growth rate from |grad| (default: 1e-2)
        mu (float): conduction decay rate (default: 1e-3)
        weight_decay (float): optional weight decay for parameters (default: 0)

    Example:
        optimizer = ARP_Optimiser(model.parameters(), lr=1e-3, alpha=1e-2, mu=1e-3)
    """

    def __init__(self, params,
                 lr=1e-3,
                 alpha=1e-2,
                 mu=1e-3,
                 weight_decay=0.0,
                 clamp_G_min=1e-4,
                 clamp_G_max=10.0):
        # Ensure all variables are properly defined and parentheses are closed
        defaults = dict(lr=lr, alpha=alpha, mu=mu,
                        weight_decay=weight_decay,
                        clamp_G_min=clamp_G_min,
                        clamp_G_max=clamp_G_max)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        # Ensure proper syntax and variable usage
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            lr = group['lr']
            alpha = group['alpha']
            mu = group['mu']
            weight_decay = group['weight_decay']
            clamp_min = group['clamp_G_min']
            clamp_max = group['clamp_G_max']
            
            # --- Warm-start G from initial gradient ---
            if 'warm_started' not in self.state:
                for p in group['params']:
                    if p.grad is not None:
                        grad = p.grad.detach().abs()
                        state = self.state[p]
                        if 'G' not in state:
                            # Initialize G based on the first gradient seen - with safety check
                            safe_alpha = max(alpha, 1e-6)
                            safe_mu = max(mu, 1e-6)
                            state['G'] = (safe_alpha / safe_mu) * grad.clamp(min=1e-5, max=10.0)
                self.state['warm_started'] = True
                print("🔥 Warm-started G_ij from initial gradient snapshot")

            for p in group['params']:
                if p.grad is None:
                    continue

                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError("ARP_Optimiser does not support sparse gradients")

                if weight_decay != 0:
                    p.data.add_(-weight_decay * p.data)

                state = self.state[p]
                if 'G' not in state:
                    state['G'] = torch.zeros_like(p.data)

                G = state['G']
                G.mul_(1 - mu).add_(alpha * grad.abs())

                if clamp_min is not None or clamp_max is not None:
                    G.clamp_(min=clamp_min, max=clamp_max)

                p.data.add_(G * grad.sign(), alpha=-lr)

        return loss

# Alias for backward compatibility
ARPOptimizer = ARP_Optimiser
