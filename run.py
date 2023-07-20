import os
import random

def generate_vrp_file_variants(original_file, num_variants=10):
    with open(original_file, 'r') as f:
        lines = f.readlines()

    # Find the start and end indices of the SALVAGE_DEMAND_SECTION
    start = lines.index('SALVAGE_DEMAND_SECTION\n')
    end = lines.index('DEPOT_SECTION\n')

    for variant in range(1, num_variants+1):
        variant_lines = lines.copy()

        # Reset all values in the salvage section to 0
        for i in range(start+1, end):
            variant_lines[i] = f'{i-start} 0\n'

        # Generate 13 random indices for nodes to salvage
        salvage_indices = random.sample(range(2, 82+1), 13)  # updated range

        # Set salvage values of the selected nodes to 1
        for idx in salvage_indices:
            variant_lines[start + idx] = f'{idx} 1\n'

        # Write the variant file
        output_dir = "/Users/e550705/workspaces/PyVRP/examples/data/"
        with open(os.path.join(output_dir, f"{os.path.splitext(os.path.basename(original_file))[0]}_{variant}.vrp"), 'w') as f:
            f.writelines(variant_lines)

# Usage:
generate_vrp_file_variants('/Users/e550705/workspaces/PyVRP/examples/data/outbound_distance_new.vrp', num_variants=1000)
