import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
import enum

# --- 0. Global Simulation Parameters (Architect: parameterization, Red-Teamer: quantitative details) ---
N_TRIALS = 200        # Number of simulated trials for each condition
N_NEURONS = 50        # Number of simulated VISp neurons
BASELINE_RATE_HZ = 10 # Hz, baseline firing rate of VISp neurons
VISUAL_RESPONSE_MAGNITUDE_HZ = 15 # Hz, increase in firing for a visual stimulus

# Arousal levels (Red-Teamer: Granularity of "Behavioral State" - discrete levels for simulation)
AROUSAL_LEVELS = [0.2, 0.5, 0.8] # Normalized factor (0-1) representing low, medium, high arousal

# Contrast levels (Red-Teamer: Specificity of "Visual Stimulus Property" - discrete levels)
CONTRAST_LEVELS = [0.3, 0.8] # Normalized factor (0-1) representing low, high contrast

# PFC Feedback strengths (Architect: configurable modules, Red-Teamer: quantitative details)
# These factors define the magnitude of the modulation.
# ACA enhances visual encoding, dependent on arousal and contrast.
ACA_MAX_ENHANCEMENT_FACTOR = 0.8 # Max proportional increase when fully active & optimal conditions
ACA_AROUSAL_DEPENDENCY_SCALE = 1.0 # How much arousal scales ACA's effect
ACA_CONTRAST_DEPENDENCY_SCALE = 0.5 # How much contrast scales ACA's effect

# ORB reduces high-contrast visual encoding.
ORB_MAX_REDUCTION_FACTOR = 0.5   # Max proportional decrease for high contrast
ORB_HIGH_CONTRAST_THRESHOLD = 0.5 # Contrast level above which ORB starts to reduce

# Noise for realism (Scientist: Adds Gaussian noise for realistic firing rates)
FIRING_RATE_NOISE_STD_PROPORTION = 0.1 # Std dev as a proportion of the mean rate

# --- 1. Enums for States and Regions (Red-Teamer: structured representation) ---
class BehavioralState(enum.Enum):
    """Represents various internal states of the organism."""
    LOW_AROUSAL = "Low Arousal"
    HIGH_AROUSAL = "High Arousal"
    # Red-Teaming Note: Could be expanded to include: ATTENTIVE, DISTRACTED, EXPLORING, etc.
    # For this simulation, we map numerical arousal levels to these conceptual states for clarity.

class VisualStimulusProperty(enum.Enum):
    """Represents properties of the visual input."""
    LOW_CONTRAST = "Low Contrast"
    HIGH_CONTRAST = "High Contrast"
    # Red-Teaming Note: Could be expanded to include: LOW_SPATIAL_FREQ, HIGH_SPATIAL_FREQ, MOTION, etc.
    # For ORB, the 'high-contrast' aspect is critical.

class PFCSubregion(enum.Enum):
    """Distinct subregions of the Prefrontal Cortex providing feedback."""
    NO_FEEDBACK = "No Feedback"
    ACA_ACTIVE = "ACA Active"
    ORB_ACTIVE = "ORB Active"

# --- 2. Core Classes for Brain Regions and Encoding (Architect: modularity, Red-Teamer: conceptual structure) ---

class VisualEncoding:
    """
    Represents the quality or strength of visual information encoded in VISp.
    For this simulation, 'strength' is explicitly mapped to 'firing_rate' (Hz).
    Scientist/Red-Teamer Note: This is a simplification. Real encoding is multi-dimensional
    (e.g., spike precision, population coding efficiency, signal-to-noise ratio).
    """
    def __init__(self, initial_firing_rate: float):
        self.firing_rate = max(0.0, initial_firing_rate) # Firing rate cannot be negative

    def enhance(self, factor: float):
        """Increases the encoding strength (firing rate)."""
        self.firing_rate *= (1 + factor)
        self.firing_rate = max(0.0, self.firing_rate) # Ensure non-negative

    def reduce(self, factor: float):
        """Decreases the encoding strength (firing rate)."""
        self.firing_rate *= (1 - factor)
        self.firing_rate = max(0.0, self.firing_rate) # Ensure non-negative

    def get_firing_rate(self) -> float:
        return self.firing_rate

    def __repr__(self):
        return f"VisualEncoding(firing_rate={self.firing_rate:.2f} Hz)"

class PrimaryVisualCortex_VISp:
    """
    Models the Primary Visual Cortex (VISp) and its modulation by PFC feedback.
    Architect: Core component of a simulation platform.
    """
    def __init__(self, baseline_rate: float, vis_response_magnitude: float):
        self.baseline_rate = baseline_rate
        self.vis_response_magnitude = vis_response_magnitude
        self.current_encoding = None
        # Red-Teaming Note: This abstraction doesn't model laminar organization directly,
        # but acknowledges its importance as a descriptor. A full simulation (Architect System 1)
        # would need 'layers' as sub-components with distinct cell types.
        self.laminar_organization_info = {
            PFCSubregion.ACA_ACTIVE: "Distinct laminar organization (e.g., input to superficial layers)",
            PFCSubregion.ORB_ACTIVE: "Distinct laminar organization (e.g., input to deeper layers)"
        }

    def receive_visual_input(self, contrast_level: float):
        """
        Simulates baseline visual input processing based on contrast.
        Initializes the visual encoding for a new trial.
        """
        base_rate = self.baseline_rate + self.vis_response_magnitude * contrast_level
        self.current_encoding = VisualEncoding(base_rate)
        # print(f"VISp received base visual input (Contrast={contrast_level:.2f}). {self.current_encoding}")

    def apply_pfc_feedback(self,
                           subregion: PFCSubregion,
                           arousal_level: float, # Using float for continuous representation
                           contrast_level: float): # Using float for continuous representation
        """
        Applies feedback from a PFC subregion, modulating VISp's visual encoding.
        This method directly embodies the core findings of the paper.
        """
        if self.current_encoding is None:
            raise ValueError("VISp must receive visual input before applying feedback.")

        # Conceptual note on laminar organization (Red-Teamer)
        # print(f"  Laminar projection for {subregion.name}: {self.laminar_organization_info.get(subregion, 'General')}")

        # Apply general arousal modulation if any, before specific PFC feedback
        # Scientist: "Arousal scales the visual response" - implemented here as a general boost
        arousal_boost = (1 + arousal_level * 0.5) # Arbitrary scaling for general arousal effect
        self.current_encoding.enhance(arousal_boost - 1) # Subtract 1 because enhance adds (1+factor)

        if subregion == PFCSubregion.ACA_ACTIVE:
            # ACA feedback enhances visual encoding, dependent on arousal and contrast.
            # Scientist: "stronger enhancement with higher arousal and contrast"
            # Red-Teamer: "Could other states or combinations be important?" -> model as interaction
            effective_enhancement = ACA_MAX_ENHANCEMENT_FACTOR \
                                  * (arousal_level * ACA_AROUSAL_DEPENDENCY_SCALE) \
                                  * (contrast_level * ACA_CONTRAST_DEPENDENCY_SCALE)

            self.current_encoding.enhance(effective_enhancement)
            # print(f"  ACA feedback applied. {self.current_encoding}")

        elif subregion == PFCSubregion.ORB_ACTIVE:
            # ORB feedback reduces *high-contrast* visual encoding.
            # Red-Teamer: "Why specifically 'high-contrast'?" - implemented as a conditional effect
            # Scientist: "reduction specifically for high contrast"
            reduction_factor = 0.0
            if contrast_level >= ORB_HIGH_CONTRAST_THRESHOLD:
                # Scale reduction by how 'high' the contrast is above the threshold
                contrast_overshoot = max(0, contrast_level - ORB_HIGH_CONTRAST_THRESHOLD) / (1 - ORB_HIGH_CONTRAST_THRESHOLD)
                reduction_factor = ORB_MAX_REDUCTION_FACTOR * contrast_overshoot

                # Red-Teaming Hypothesis/Question: Is ORB reduction also modulated by arousal?
                # The abstract implies this for ACA, but highlights specifically state "high-contrast" for ORB.
                # Here, we *don't* make it arousal-dependent for ORB, strictly following the highlight.
                # If we were to hypothesize:
                # if arousal_level > SOME_AROUSAL_THRESHOLD:
                #     reduction_factor *= 1.1 # Slightly more reduction under high arousal (hypothetical)
                #     print("  ORB: (Hypothesis) High arousal slightly amplifies high-contrast reduction.")

            self.current_encoding.reduce(reduction_factor)
            # print(f"  ORB feedback applied. {self.current_encoding}")
        # else: NO_FEEDBACK implies only general arousal modulation already applied.

        # Add some random noise (e.g., Gaussian noise for rate)
        simulated_rate = np.random.normal(self.current_encoding.get_firing_rate(),
                                          self.current_encoding.get_firing_rate() * FIRING_RATE_NOISE_STD_PROPORTION)
        self.current_encoding.firing_rate = max(0, simulated_rate) # Firing rate cannot be negative

class PrefrontalCortex_PFC:
    """
    Models the Prefrontal Cortex, sending feedback signals to VISp.
    (Simplified: Does not model internal PFC activity, only its output pathways).
    Architect: Represents a high-level module interacting with VISp.
    """
    def __init__(self, target_visp: PrimaryVisualCortex_VISp):
        self.target_visp = target_visp

    def send_feedback(self,
                      subregion: PFCSubregion,
                      behavioral_state_level: float, # Maps to AROUSAL_LEVELS
                      visual_property_level: float): # Maps to CONTRAST_LEVELS
        """
        Dispatches feedback from a specific PFC subregion to the target VISp.
        Scientist: "PFC feedback" is what's manipulated.
        """
        self.target_visp.apply_pfc_feedback(subregion, behavioral_state_level, visual_property_level)

# --- 3. Data Simulation & Analysis Workflow (Scientist: main goal, Architect: data management, Red-Teamer: validation) ---

def run_full_simulation():
    """
    Orchestrates the simulation, data collection, plotting, and statistical analysis.
    Architect: Represents the main execution flow of a simulation platform.
    """
    print("Initializing simulation environment...")
    visp_model = PrimaryVisualCortex_VISp(BASELINE_RATE_HZ, VISUAL_RESPONSE_MAGNITUDE_HZ)
    pfc_controller = PrefrontalCortex_PFC(visp_model)

    simulation_results = []

    # Iterate through all conditions to build the dataset
    print("Simulating VISp neuron activity data across conditions...")
    for trial_idx in range(N_TRIALS):
        for neuron_idx in range(N_NEURONS):
            for pfc_type in PFCSubregion: # Includes 'No_Feedback', 'ACA_Active', 'ORB_Active'
                for arousal_level_val in AROUSAL_LEVELS:
                    for contrast_level_val in CONTRAST_LEVELS:

                        # 1. VISp receives baseline visual input for the current contrast
                        visp_model.receive_visual_input(contrast_level_val)

                        # 2. PFC sends feedback, which modulates VISp encoding
                        # (General arousal modulation is applied inside apply_pfc_feedback, before specific PFC effect)
                        if pfc_type != PFCSubregion.NO_FEEDBACK: # Only apply specific PFC feedback if not 'No_Feedback'
                            pfc_controller.send_feedback(pfc_type, arousal_level_val, contrast_level_val)
                        else:
                            # If no specific PFC feedback, still apply general arousal modulation and noise
                            # This is done by calling apply_pfc_feedback with NO_FEEDBACK, as the general arousal logic is inside.
                            visp_model.apply_pfc_feedback(PFCSubregion.NO_FEEDBACK, arousal_level_val, contrast_level_val)


                        # Store the results for this specific trial/neuron/condition
                        simulation_results.append({
                            'Trial': trial_idx,
                            'Neuron': neuron_idx,
                            'PFC_Feedback': pfc_type.value,
                            'Arousal_Level': arousal_level_val,
                            'Contrast_Level': contrast_level_val,
                            'Firing_Rate_Hz': visp_model.current_encoding.get_firing_rate()
                        })

    simulated_df = pd.DataFrame(simulation_results)
    print("Simulation complete. Data head:")
    print(simulated_df.head())
    print(f"Total data points: {len(simulated_df)}")

    # 4. Visualization of Findings (Scientist & Architect: interactive visualization)
    print("\nPlotting PFC feedback effects on VISp firing rates...")
    plt.figure(figsize=(16, 7)) # Increased figure size

    # Plot 1: ACA's effect - Firing Rate vs. Arousal, split by Contrast & PFC_Feedback
    plt.subplot(1, 2, 1)
    sns.lineplot(data=simulated_df[simulated_df['PFC_Feedback'].isin([PFCSubregion.NO_FEEDBACK.value, PFCSubregion.ACA_ACTIVE.value])],
                 x='Arousal_Level', y='Firing_Rate_Hz', hue='PFC_Feedback', style='Contrast_Level', marker='o', errorbar='sd')
    plt.title('VISp Firing Rate modulated by ACA, Arousal & Contrast')
    plt.xlabel('Arousal Level (Normalized)')
    plt.ylabel('Average Firing Rate (Hz)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title='Condition')

    # Plot 2: ORB's effect - Firing Rate vs. Contrast, split by Arousal & PFC_Feedback
    plt.subplot(1, 2, 2)
    sns.lineplot(data=simulated_df[simulated_df['PFC_Feedback'].isin([PFCSubregion.NO_FEEDBACK.value, PFCSubregion.ORB_ACTIVE.value])],
                                  x='Contrast_Level', y='Firing_Rate_Hz', hue='PFC_Feedback', style='Arousal_Level', marker='o', errorbar='sd')
    plt.title('VISp Firing Rate modulated by ORB and Contrast')
    plt.xlabel('Contrast Level (Normalized)')
    plt.ylabel('Average Firing Rate (Hz)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title='Condition')

    plt.tight_layout()
    plt.show()

    # 5. Statistical Tests (Scientist: validation, Architect: reproducibility)
    print("\n--- Specific Statistical Comparisons reflecting Highlights ---")

    # ACA Test: ACA_Active vs No_Feedback at high arousal, high contrast
    # "ACA feedback: Enhances visual encoding, dependent on arousal and contrast."
    aca_high_arousal_high_contrast_active = simulated_df[
        (simulated_df['PFC_Feedback'] == PFCSubregion.ACA_ACTIVE.value) &
        (simulated_df['Arousal_Level'] == AROUSAL_LEVELS[-1]) &
        (simulated_df['Contrast_Level'] == CONTRAST_LEVELS[-1])
    ]['Firing_Rate_Hz']

    no_feedback_high_arousal_high_contrast = simulated_df[
        (simulated_df['PFC_Feedback'] == PFCSubregion.NO_FEEDBACK.value) &
        (simulated_df['Arousal_Level'] == AROUSAL_LEVELS[-1]) &
        (simulated_df['Contrast_Level'] == CONTRAST_LEVELS[-1])
    ]['Firing_Rate_Hz']

    t_aca, p_aca = stats.ttest_ind(aca_high_arousal_high_contrast_active,
                                  no_feedback_high_arousal_high_contrast,
                                  equal_var=False) # Welch's t-test, assuming unequal variances
    print(f"ACA_Active vs No_Feedback (High Arousal, High Contrast): "
          f"t={t_aca:.2f}, p={p_aca:.4f} "
          f"(ACA enhances visual encoding? {'YES' if t_aca > 0 and p_aca < 0.05 else 'NO, or effect is not significant or negative'}).")

    # ORB Test: ORB_Active vs No_Feedback at high contrast
    # "ORB feedback: Reduces high-contrast visual encoding."
    orb_high_contrast_active = simulated_df[
        (simulated_df['PFC_Feedback'] == PFCSubregion.ORB_ACTIVE.value) &
        (simulated_df['Contrast_Level'] == CONTRAST_LEVELS[-1])
    ]['Firing_Rate_Hz']

    no_feedback_high_contrast = simulated_df[
        (simulated_df['PFC_Feedback'] == PFCSubregion.NO_FEEDBACK.value) &
        (simulated_df['Contrast_Level'] == CONTRAST_LEVELS[-1])
    ]['Firing_Rate_Hz']

    t_orb, p_orb = stats.ttest_ind(orb_high_contrast_active,
                                  no_feedback_high_contrast,
                                  equal_var=False) # Welch's t-test
    print(f"ORB_Active vs No_Feedback (High Contrast): "
          f"t={t_orb:.2f}, p={p_orb:.4f} "
          f"(ORB reduces high-contrast visual encoding? {'YES' if t_orb < 0 and p_orb < 0.05 else 'NO, or effect is not significant or positive'}).")

    # Conceptual note on advanced statistics (Scientist)
    print("\nConceptual note: For real data, consider ANOVA or Mixed-Effects Models for robust analysis of interaction effects between multiple factors.")


if __name__ == "__main__":
    run_full_simulation()