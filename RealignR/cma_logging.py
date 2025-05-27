def log_cma_memory(writer, cma_layer, global_step):
    """
    Log CMA curve memory for each class as a histogram.
    Defensive: ensure memory is on CPU before numpy conversion, with error print.
    """
    if hasattr(cma_layer, 'curve_memory'):
        try:
            mem = cma_layer.curve_memory.detach().cpu().numpy()
        except Exception as e:
            print("Error accessing curve_memory:", e)
            print("curve_memory device:", cma_layer.curve_memory.device)
            raise
        for i in range(mem.shape[0]):
            writer.add_histogram(f"CMA/memory_class_{i}", mem[i], global_step)
