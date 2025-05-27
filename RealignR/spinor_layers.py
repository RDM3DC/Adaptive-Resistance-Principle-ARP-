import torch
from clifford import Cl
import numpy as np

# Clifford Algebra (Cl(5)) setup - can be made configurable or passed in
layout, blades = Cl(5)
e1, e2, e3, e4, e5 = blades['e1'], blades['e2'], blades['e3'], blades['e4'], blades['e5']

# Spinor layer
class SpinorLayer:
    def __init__(self, num_layers=2, num_classes=100):
        self.num_layers = num_layers
        # Initialize rotors using the global `layout` from Cl(5)
        self.rotors = {i: [layout.scalar for _ in range(num_layers)] for i in range(num_classes)}
        self.memory = {i: [] for i in range(num_classes)}

    def normalize_rotor(self, S):
        # Ensure S is a Clifford multivector
        if not hasattr(S, 'value') or not hasattr(S, 'grades'): # .grades is a method
            # print(f"Warning: normalize_rotor received non-multivector S: {type(S)}")
            return S # Or raise an error if S must be a multivector

        s_s_tilde = S * ~S # This is a MultiVector
        
        # Extract the scalar part (grade 0) of S * ~S
        # s_s_tilde(0) returns a MultiVector containing only the grade 0 part
        scalar_part_mv = s_s_tilde(0) 
        raw_value = scalar_part_mv.value # This is the numpy array of coefficients for the scalar part

        # If scalar_part_mv is purely grade 0 (which it should be by definition),
        # its .value array will be [actual_scalar_coeff, 0, 0, ...].
        # The actual scalar coefficient is the first element.
        if isinstance(raw_value, np.ndarray) and raw_value.ndim == 1 and raw_value.size > 0:
            # This is the expected case for the .value of a scalar multivector in an algebra
            # with multiple basis elements (like Cl(5) where .value is a 32-element array for a scalar).
            norm_val_scalar = raw_value[0]
        elif isinstance(raw_value, (float, int)): 
            # This case would be if .value itself returned a Python scalar, less common for full algebra.
            norm_val_scalar = raw_value
        else:
            # This means raw_value from scalar_part_mv.value is not a 1D numpy array or a Python scalar.
            s_s_tilde_grades = s_s_tilde.grades()
            raise ValueError(
                f"Rotor normalization failed: scalar_part_mv.value is of unexpected type or shape. "
                f"Type: {type(raw_value)}, Shape: {getattr(raw_value, 'shape', 'N/A')}. "
                f"S*~S grades: {s_s_tilde_grades}. scalar_part_mv grades: {scalar_part_mv.grades()}"
            )
        
        # Ensure norm_val_scalar is a float/int after extraction
        if not isinstance(norm_val_scalar, (float, int, np.floating, np.integer)):
            raise ValueError(f"Extracted norm_val_scalar is not a numerical type: {type(norm_val_scalar)}, value: {norm_val_scalar}")

        # Handle potential negative values due to numerical precision
        if norm_val_scalar < -1e-9: # Allow for small negative due to precision but warn if significant
            # print(f"Warning: norm_val_scalar for S*~S is significantly negative ({norm_val_scalar}). Taking absolute value.")
            norm_val_scalar = abs(norm_val_scalar)
        elif norm_val_scalar < 0: # If slightly negative, treat as zero to avoid issues with sqrt
            norm_val_scalar = 0.0
            
        norm = norm_val_scalar ** 0.5
        
        if norm > 1e-10:
            return S / norm
        else:
            # print("Warning: Rotor norm is close to zero or zero. Returning original rotor.")
            return S

    def tensor_to_vector(self, tensor):
        tensor = tensor.detach().cpu()
        # Use the global `blades`
        return sum(float(tensor[j]) * blades[f'e{j+1}'] for j in range(tensor.size(0)))

    def vector_to_tensor(self, vector, device):
        # Use the global `blades`
        # Ensure vector components are extracted correctly, assuming vector is a Cl(5) multivector
        result = [float((vector | blades[f'e{j+1}']).value[0] if hasattr((vector | blades[f'e{j+1}']), 'value') and isinstance((vector | blades[f'e{j+1}']).value, np.ndarray) and (vector | blades[f'e{j+1}']).value.size > 0 else 0.0) for j in range(5)]
        return torch.tensor(result, device=device, dtype=torch.float32)

    def apply_rotor(self, vector, rotors):
        v = self.tensor_to_vector(vector)
        for rotor in rotors:
            # Norm calculation for v (a Clifford multivector)
            # Ensure components are correctly extracted for norm calculation
            v_coeffs = np.array([float((v | blades[f'e{j+1}']).value[0] if hasattr((v | blades[f'e{j+1}']), 'value') and isinstance((v | blades[f'e{j+1}']).value, np.ndarray) and (v | blades[f'e{j+1}']).value.size > 0 else 0.0) for j in range(5)])
            norm = np.linalg.norm(v_coeffs)
            if np.isfinite(norm) and norm > 1e-6:
                v = v / norm
            v = rotor * v * ~rotor
        return self.vector_to_tensor(v, vector.device)

    def forward(self, vectors, labels):
        transformed = []
        for vector, label in zip(vectors, labels):
            label_int = int(label.item())
            # Ensure rotor exists for the label, handle if not (e.g. new class)
            if label_int not in self.rotors:
                # Initialize rotors for new class on-the-fly or raise error
                self.rotors[label_int] = [layout.scalar for _ in range(self.num_layers)]
                self.memory[label_int] = []
            transformed.append(self.apply_rotor(vector, self.rotors[label_int]))
        return torch.stack(transformed)

    def update_rotors(self, vectors, targets, labels, learning_rate=0.1):
        transformed = self.forward(vectors, labels)
        errors = targets - transformed
        error_norms = torch.norm(errors, dim=1)
        # Add epsilon to prevent division by zero if norms are zero
        alignment = torch.sum(transformed * targets, dim=1) / (
            torch.norm(transformed, dim=1) * torch.norm(targets, dim=1) + 1e-10
        )
        # Ensure alignment is a scalar for dynamic_lr calculation
        dynamic_lr = learning_rate * (1 - alignment.mean().item() if alignment.numel() > 0 else 0.0)

        for i, (vector, error, label) in enumerate(zip(vectors, errors, labels)):
            label_int = int(label.item())
            if error_norms[i] > 1e-10:
                v = self.tensor_to_vector(vector)
                err = self.tensor_to_vector(error)
                # Ensure (v ^ err) results in a bivector suitable for .normal()
                delta_T_bivector = (v ^ err)
                # Check if delta_T_bivector is zero or not a bivector before .normal()
                if hasattr(delta_T_bivector, 'normal') and np.any([coeff != 0 for coeff in delta_T_bivector.value]): # Check if it's not a zero multivector
                    delta_T = dynamic_lr * delta_T_bivector.normal()
                    # Ensure delta_T can be exponentiated and is compatible with rotor multiplication
                    if hasattr(delta_T, 'exp'):
                         self.rotors[label_int][-1] = self.normalize_rotor(delta_T.exp() * self.rotors[label_int][-1])
                    else:
                        # Handle case where delta_T is not exponentiable (e.g. scalar)
                        # This might indicate an issue in logic or data
                        pass # Or log a warning
                else:
                    # Handle case where (v^err) is zero or not normalizable
                    pass # Or log a warning

        for label_val in torch.unique(labels).cpu().numpy():
            label_int = int(label_val)
            if label_int in self.rotors: # Ensure key exists
                 self.memory[label_int].append([r for r in self.rotors[label_int]])
