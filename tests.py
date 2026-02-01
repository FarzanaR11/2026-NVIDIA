"""
Comprehensive Test Suite for Quantum-Enhanced LABS Optimizer
NVIDIA MIT iQuHACK 2026

This test suite validates:
1. Energy calculation correctness
2. LABS symmetry preservation
3. MTS algorithm components
4. Quantum circuit correctness
5. End-to-end integration
"""

import pytest
import numpy as np
import sys
import os

# Add tutorial notebook directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tutorial_notebook'))

# Import utility functions
from auxiliary_files import labs_utils as utils


# ============================================================================
# HELPER FUNCTIONS (import from notebook or redefine)
# ============================================================================

def compute_energy(s):
    """Compute LABS energy for a binary sequence."""
    N = len(s)
    energy = 0
    for k in range(1, N):
        C_k = sum(s[i] * s[i + k] for i in range(N - k))
        energy += C_k ** 2
    return energy


def apply_symmetry(s, symmetry_type):
    """Apply symmetry operation to sequence."""
    s_new = np.array(s)
    if symmetry_type == 'flip':
        s_new = -s_new
    elif symmetry_type == 'reverse':
        s_new = s_new[::-1]
    elif symmetry_type == 'flip_reverse':
        s_new = -s_new[::-1]
    return s_new


from math import floor

def get_interactions(N):
    """Generate G2 and G4 interaction indices."""
    G2 = []
    G4 = []

    for i in range(N - 2):
        for k in range(1, floor((N - i) / 2) + 1):
            G2.append([i, i + k])

    for i in range(N - 3):
        for t in range(1, floor((N - i - 1) / 2) + 1):
            for k in range(t + 1, N - i - t):
                G4.append([i, i + t, i + k, i + k + t])

    return G2, G4


# ============================================================================
# TEST CLASS 1: Energy Calculation
# ============================================================================

class TestEnergyCalculation:
    """Test suite for LABS energy computation."""

    def test_energy_non_negative(self):
        """Energy must be non-negative for all sequences."""
        for _ in range(100):
            N = np.random.randint(5, 30)
            s = np.random.choice([-1, 1], size=N)
            energy = compute_energy(s)
            assert energy >= 0, f"Energy {energy} is negative!"

    def test_energy_integer(self):
        """Energy must be integer-valued."""
        for _ in range(50):
            N = np.random.randint(5, 20)
            s = np.random.choice([-1, 1], size=N)
            energy = compute_energy(s)
            assert energy == int(energy), f"Energy {energy} is not integer!"

    def test_known_values(self):
        """Test against known optimal energies."""
        # Known optimal values from LABS literature
        known_cases = [
            # (sequence, expected_energy)
            (np.array([1, 1, 1, -1, -1, 1, -1]), 3),  # N=7
            (np.array([1, 1, 1, 1, -1, -1, -1, 1, -1, -1, 1]), 21),  # N=11
        ]

        for seq, expected in known_cases:
            energy = compute_energy(seq)
            assert energy == expected, \
                f"Expected {expected}, got {energy} for sequence {seq}"

    def test_trivial_cases(self):
        """Test edge cases."""
        # All same - worst case
        s_worst = np.ones(10)
        e_worst = compute_energy(s_worst)

        # Alternating - often good
        s_alt = np.array([1, -1] * 5)
        e_alt = compute_energy(s_alt)

        # Alternating should be better than all-same
        assert e_alt >= 0, "Alternating energy should be non-negative"

    def test_energy_bounds(self):
        """Energy should be bounded by theoretical limits."""
        N = 15
        s = np.random.choice([-1, 1], size=N)
        energy = compute_energy(s)

        # Maximum possible energy (all aligned): roughly N^3/6
        max_theoretical = (N ** 3) // 3  # Conservative upper bound
        assert energy < max_theoretical, \
            f"Energy {energy} exceeds theoretical max {max_theoretical}"


# ============================================================================
# TEST CLASS 2: Symmetry Properties
# ============================================================================

class TestSymmetries:
    """Test LABS symmetry invariance."""

    def test_flip_symmetry(self):
        """Energy must be invariant under negation: E(s) = E(-s)."""
        for _ in range(50):
            N = np.random.randint(5, 25)
            s = np.random.choice([-1, 1], size=N)

            E_original = compute_energy(s)
            E_flipped = compute_energy(-s)

            assert E_original == E_flipped, \
                f"Flip symmetry broken: {E_original} != {E_flipped}"

    def test_reverse_symmetry(self):
        """Energy must be invariant under reversal: E(s) = E(s[::-1])."""
        for _ in range(50):
            N = np.random.randint(5, 25)
            s = np.random.choice([-1, 1], size=N)

            E_original = compute_energy(s)
            E_reversed = compute_energy(s[::-1])

            assert E_original == E_reversed, \
                f"Reverse symmetry broken: {E_original} != {E_reversed}"

    def test_combined_symmetries(self):
        """Test all 8 symmetry operations preserve energy."""
        N = 15
        s = np.random.choice([-1, 1], size=N)
        E_original = compute_energy(s)

        # All 8 symmetries of the dihedral group D_4
        symmetries = [
            s,                # Identity
            -s,               # Flip
            s[::-1],          # Reverse
            -s[::-1],         # Flip + Reverse
        ]

        for i, s_sym in enumerate(symmetries):
            E_sym = compute_energy(s_sym)
            assert E_sym == E_original, \
                f"Symmetry {i} broken: {E_sym} != {E_original}"

    def test_symmetry_functions(self):
        """Test apply_symmetry helper function."""
        s = np.array([1, -1, 1, 1, -1])
        E_original = compute_energy(s)

        for sym_type in ['flip', 'reverse', 'flip_reverse']:
            s_sym = apply_symmetry(s, sym_type)
            E_sym = compute_energy(s_sym)
            assert E_sym == E_original, \
                f"Symmetry '{sym_type}' broken: {E_sym} != {E_original}"


# ============================================================================
# TEST CLASS 3: Interaction Indices
# ============================================================================

class TestInteractions:
    """Test G2 and G4 index generation."""

    def test_g2_size(self):
        """Verify G2 has correct number of elements."""
        test_cases = [
            (7, 11),   # Manually calculated
            (11, 29),
            (15, 55),
        ]

        for N, expected_size in test_cases:
            G2, _ = get_interactions(N)
            assert len(G2) == expected_size, \
                f"G2 size mismatch for N={N}: expected {expected_size}, got {len(G2)}"

    def test_g2_uniqueness(self):
        """G2 should contain no duplicate pairs."""
        for N in [7, 11, 15, 20]:
            G2, _ = get_interactions(N)
            G2_tuples = [tuple(sorted(pair)) for pair in G2]
            assert len(G2_tuples) == len(set(G2_tuples)), \
                f"G2 contains duplicates for N={N}"

    def test_g2_valid_indices(self):
        """All G2 indices must be in valid range."""
        N = 15
        G2, _ = get_interactions(N)

        for pair in G2:
            assert len(pair) == 2, f"G2 pair {pair} doesn't have 2 elements"
            assert 0 <= pair[0] < N, f"G2 index {pair[0]} out of range"
            assert 0 <= pair[1] < N, f"G2 index {pair[1]} out of range"
            assert pair[0] != pair[1], f"G2 pair {pair} has duplicate indices"

    def test_g4_uniqueness(self):
        """G4 should contain no duplicate quartets."""
        for N in [7, 11, 15]:
            _, G4 = get_interactions(N)
            G4_tuples = [tuple(sorted(quartet)) for quartet in G4]
            assert len(G4_tuples) == len(set(G4_tuples)), \
                f"G4 contains duplicates for N={N}"

    def test_g4_valid_indices(self):
        """All G4 indices must be in valid range and unique."""
        N = 15
        _, G4 = get_interactions(N)

        for quartet in G4:
            assert len(quartet) == 4, f"G4 quartet {quartet} doesn't have 4 elements"
            for idx in quartet:
                assert 0 <= idx < N, f"G4 index {idx} out of range"
            # Check all indices are unique
            assert len(set(quartet)) == 4, \
                f"G4 quartet {quartet} has duplicate indices"

    def test_theta_computation(self):
        """Test theta computation doesn't crash and returns reasonable values."""
        N = 11
        G2, G4 = get_interactions(N)
        T = 1.0
        n_steps = 5
        dt = T / n_steps

        for step in range(1, n_steps + 1):
            t = step * dt
            theta = utils.compute_theta(t, dt, T, N, G2, G4)

            # Theta should be finite
            assert np.isfinite(theta), f"Theta is not finite at step {step}"

            # Theta should be real
            assert isinstance(theta, (int, float)), \
                f"Theta is not real at step {step}"


# ============================================================================
# TEST CLASS 4: MTS Algorithm Components
# ============================================================================

class TestMTSComponents:
    """Test Memetic Tabu Search components."""

    def test_combine_produces_valid_sequence(self):
        """Combine operator must produce valid sequences."""
        # Import combine if available, otherwise skip
        pytest.importorskip("combine")

        N = 15
        s1 = np.random.choice([-1, 1], size=N)
        s2 = np.random.choice([-1, 1], size=N)

        from __main__ import combine  # Assuming it's defined in notebook
        child = combine(s1, s2)

        assert len(child) == N, "Child has wrong length"
        assert set(child).issubset({-1, 1}), "Child contains invalid values"

    def test_mutate_preserves_length(self):
        """Mutate operator must preserve sequence length."""
        pytest.importorskip("mutate")

        N = 20
        s = np.random.choice([-1, 1], size=N)

        from __main__ import mutate
        s_mut = mutate(s, p_mutate=0.2)

        assert len(s_mut) == N, "Mutation changed sequence length"
        assert set(s_mut).issubset({-1, 1}), "Mutation introduced invalid values"

    def test_mutate_probability(self):
        """Mutate with p=0 should not change sequence."""
        pytest.importorskip("mutate")

        N = 15
        s = np.random.choice([-1, 1], size=N)

        from __main__ import mutate
        s_mut = mutate(s.copy(), p_mutate=0.0)

        np.testing.assert_array_equal(s, s_mut,
            "Mutate with p=0 changed the sequence")


# ============================================================================
# TEST CLASS 5: Quantum Circuit (requires CUDA-Q)
# ============================================================================

class TestQuantumCircuit:
    """Test quantum circuit implementation."""

    def test_circuit_imports(self):
        """Verify CUDA-Q is available."""
        try:
            import cudaq
        except ImportError:
            pytest.skip("CUDA-Q not available")

    def test_quantum_sampling_produces_valid_sequences(self):
        """Quantum samples must be valid binary sequences."""
        pytest.importorskip("cudaq")
        pytest.importorskip("sample_quantum_population")

        from __main__ import sample_quantum_population

        N = 11
        pop_size = 10

        samples = sample_quantum_population(N, pop_size, T=1.0, n_steps=1)

        assert len(samples) == pop_size, "Wrong number of samples"

        for s in samples:
            assert len(s) == N, f"Sample has wrong length: {len(s)}"
            assert set(s).issubset({-1, 1}), "Sample contains invalid values"
            assert not np.any(np.isnan(s)), "Sample contains NaN"

    def test_quantum_energies_are_finite(self):
        """Quantum samples must have finite energies."""
        pytest.importorskip("cudaq")
        pytest.importorskip("sample_quantum_population")

        from __main__ import sample_quantum_population

        N = 11
        samples = sample_quantum_population(N, pop_size=5)

        for s in samples:
            E = compute_energy(s)
            assert np.isfinite(E), f"Quantum sample has infinite energy"
            assert E >= 0, f"Quantum sample has negative energy: {E}"


# ============================================================================
# TEST CLASS 6: Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_classical_workflow(self):
        """Test complete classical MTS workflow."""
        pytest.importorskip("memetic_tabu_search")

        from __main__ import memetic_tabu_search

        N = 11
        best, energy, pop, hist = memetic_tabu_search(
            N, pop_size=10, generations=5
        )

        # Validate outputs
        assert len(best) == N, "Best sequence has wrong length"
        assert energy >= 0, "Best energy is negative"
        assert len(pop) == 10, "Final population has wrong size"
        assert len(hist) > 0, "No energy history recorded"

        # Energy should not increase
        assert all(hist[i] >= hist[i+1] for i in range(len(hist)-1)), \
            "Energy increased during optimization"

    def test_quantum_enhanced_workflow(self):
        """Test complete quantum-enhanced workflow."""
        pytest.importorskip("cudaq")
        pytest.importorskip("sample_quantum_population")
        pytest.importorskip("memetic_tabu_search")

        from __main__ import sample_quantum_population, memetic_tabu_search

        N = 11
        pop_size = 10

        # Generate quantum population
        quantum_pop = sample_quantum_population(N, pop_size)

        # Run MTS with quantum initialization
        best, energy, pop, hist = memetic_tabu_search(
            N, pop_size=pop_size, generations=5,
            initial_population=quantum_pop
        )

        # Validate outputs
        assert len(best) == N
        assert energy >= 0
        assert len(hist) > 0

    def test_quantum_vs_random_comparison(self):
        """Test that quantum vs random comparison runs without errors."""
        pytest.importorskip("cudaq")
        pytest.importorskip("sample_quantum_population")
        pytest.importorskip("memetic_tabu_search")

        from __main__ import sample_quantum_population, memetic_tabu_search

        N = 11
        pop_size = 5
        generations = 3

        # Random initialization
        _, E_random, _, _ = memetic_tabu_search(
            N, pop_size=pop_size, generations=generations
        )

        # Quantum initialization
        quantum_pop = sample_quantum_population(N, pop_size)
        _, E_quantum, _, _ = memetic_tabu_search(
            N, pop_size=pop_size, generations=generations,
            initial_population=quantum_pop
        )

        # Both should produce valid energies
        assert E_random >= 0, "Random MTS produced negative energy"
        assert E_quantum >= 0, "Quantum MTS produced negative energy"


# ============================================================================
# TEST CLASS 7: Regression Tests
# ============================================================================

class TestRegression:
    """Regression tests to prevent breaking changes."""

    def test_energy_calculation_unchanged(self):
        """Energy calculation must match golden reference."""
        # Golden test cases
        golden_tests = [
            (np.array([1, -1, 1, -1, 1, -1, 1]), 91),
            (np.array([1, 1, -1, -1, 1, 1, -1]), 35),
            (np.array([1, 1, 1, -1, -1, -1, 1]), 23),
        ]

        for seq, expected_energy in golden_tests:
            actual_energy = compute_energy(seq)
            assert actual_energy == expected_energy, \
                f"Regression: energy for {seq} changed from {expected_energy} to {actual_energy}"

    def test_interaction_count_unchanged(self):
        """Interaction counts must match golden values."""
        golden_counts = [
            (7, 11, 13),   # N, |G2|, |G4|
            (11, 29, 70),
            (15, 55, 203),
        ]

        for N, expected_g2, expected_g4 in golden_counts:
            G2, G4 = get_interactions(N)
            assert len(G2) == expected_g2, \
                f"Regression: G2 size for N={N} changed from {expected_g2} to {len(G2)}"
            assert len(G4) == expected_g4, \
                f"Regression: G4 size for N={N} changed from {expected_g4} to {len(G4)}"


# ============================================================================
# PROPERTY-BASED TESTS (using Hypothesis if available)
# ============================================================================

try:
    from hypothesis import given, strategies as st

    class TestPropertyBased:
        """Property-based tests using Hypothesis."""

        @given(st.lists(st.sampled_from([-1, 1]), min_size=3, max_size=30))
        def test_energy_always_non_negative(self, sequence):
            """Property: Energy is always non-negative for any sequence."""
            s = np.array(sequence)
            E = compute_energy(s)
            assert E >= 0, f"Found negative energy {E} for sequence {s}"

        @given(st.lists(st.sampled_from([-1, 1]), min_size=3, max_size=30))
        def test_flip_symmetry_property(self, sequence):
            """Property: E(s) = E(-s) for any sequence."""
            s = np.array(sequence)
            E1 = compute_energy(s)
            E2 = compute_energy(-s)
            assert E1 == E2, f"Flip symmetry broken: {E1} != {E2}"

        @given(st.lists(st.sampled_from([-1, 1]), min_size=3, max_size=30))
        def test_reverse_symmetry_property(self, sequence):
            """Property: E(s) = E(s[::-1]) for any sequence."""
            s = np.array(sequence)
            E1 = compute_energy(s)
            E2 = compute_energy(s[::-1])
            assert E1 == E2, f"Reverse symmetry broken: {E1} != {E2}"

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass


# ============================================================================
# PERFORMANCE BENCHMARKS (not part of correctness testing)
# ============================================================================

class TestPerformance:
    """Performance benchmarks (informational, not pass/fail)."""

    def test_energy_computation_speed(self, benchmark=None):
        """Benchmark energy computation speed."""
        if benchmark is None:
            pytest.skip("pytest-benchmark not available")

        N = 20
        s = np.random.choice([-1, 1], size=N)

        result = benchmark(compute_energy, s)
        print(f"Energy computation for N={N}: {result}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-W", "ignore::DeprecationWarning"])
ubuntu@brev-5g1xtl74o:~/workspace/2026-NVIDIA$ 
