# Product Requirements Document (PRD)

**Project Name:** QE-LABS-Optimizer (Quantum-Enhanced LABS Optimizer)
**Team Name:** Quantum Brainwave
**GitHub Repository:** https://github.com/FarzanaR11/2026-NVIDIA

---

## 1. Team Roles & Responsibilities

| Role | Name | GitHub Handle | Discord Handle
| :--- | :--- | :--- | :--- |
| **Project Lead** (Architect) | Farzana Rahman | @FarzanaR11 | farzana3301 |
| **Technical Marketing PIC** (Storyteller) | Shams Ul Arefin Nibir | @arefin-nibir | Shams Nibir |

---

## 2. The Architecture
**Owner:** Project Lead

### Choice of Quantum Algorithm

* **Algorithm:** Digitized Counteradiabatic (CD) Quantum Optimization with Trotterized Evolution

* **Motivation:**
  * **Gate Efficiency:** The counteradiabatic approach requires only 236K entangling gates for N=67, compared to 1.4M gates for QAOA. This 6x reduction in gate count is critical for:
    - Reducing quantum circuit depth (better noise resilience)
    - Faster simulation times on GPU backends
    - More feasible deployment on near-term quantum hardware

  * **Problem-Specific Physics:** The CD approach leverages the adiabatic gauge potential A(λ) which encodes problem structure directly from the LABS Hamiltonian. This physics-informed design provides:
    - Better suppression of diabatic transitions
    - More efficient exploration of the energy landscape
    - Natural handling of LABS symmetries through the Hamiltonian structure

  * **Hybrid-First Design:** Unlike pure quantum approaches, CD optimization is designed for hybrid workflows:
    - Produces approximate solutions that seed classical optimization
    - Complements classical MTS rather than replacing it
    - Proven scaling advantage: O(1.24^N) for QE-MTS vs O(1.34^N) for classical MTS

  * **Research Validation:** The approach is validated in "Scaling advantage with quantum-enhanced memetic tabu search for LABS" (arXiv:2511.04553v1), demonstrating promise for N≥47.

### Literature Review

**Primary Reference:**
* **Title:** "Scaling advantage with quantum-enhanced memetic tabu search for LABS"
* **Authors:** Kipu Quantum, University of the Basque Country, NVIDIA
* **Link:** https://arxiv.org/html/2511.04553v1
* **Relevance:**
  - Provides the complete counteradiabatic circuit implementation (Equation 15)
  - Demonstrates QE-MTS scales as O(1.24^N) vs MTS O(1.34^N)
  - Shows outlier performance where QE-MTS can be much faster than classical
  - Validates approach on problem sizes N=27 to N=37

**Supporting References:**
* **Title:** "Parallel MTS by JPMorgan Chase"
* **Link:** arXiv:2504.00987
* **Relevance:** Provides baseline MTS implementation details including combine/mutate operators and tabu search strategy

* **Title:** "CUDA-Q Academic - Quick Start to Quantum"
* **Relevance:** Reference for implementing rotation gates, controlled operations, and circuit sampling

### Algorithm Implementation Details

**Hamiltonian Encoding:**
The LABS problem is encoded as:
```
H_f = 2 Σ σ_i^z Σ σ_{i+k}^z + 4 Σ σ_i^z Σ σ_{i+t}^z σ_{i+k}^z σ_{i+k+t}^z
```

**Evolution Operator:**
Using first-order CD approximation in impulse regime:
```
U(0,T) = Π [Π R_YZ(4θ) R_ZY(4θ)] × [Π R_YZZZ(8θ) R_ZYZZ(8θ) R_ZZYZ(8θ) R_ZZZY(8θ)]
```

Where θ(t) = dt × α(t) × λ'(t) with:
- λ(t) = sin²(πt/2T) (annealing schedule)
- α(t) = -Γ₁(t)/Γ₂(t) (gauge potential approximation)

---

## 3. The Acceleration Strategy
**Owner:** GPU Acceleration PIC

### Quantum Acceleration (CUDA-Q)

**Strategy:** Multi-stage GPU scaling approach

* **Stage 1 - Single GPU (Phase 1):**
  - Target: qBraid with CUDA-Q CPU simulator for development
  - Use: `cudaq.sample()` with default backend for N≤20
  - Goal: Validate correctness, establish baseline

* **Stage 2 - Single GPU (Phase 2):**
  - Target: Brev L4 instance with `nvidia` backend
  - Use: Single GPU state vector simulation for N=20-35
  - Optimization: Batch sampling (1000+ shots) to amortize overhead
  - Expected: 10-20x speedup over CPU simulation

* **Stage 3 - Multi-GPU (Stretch Goal):**
  - Target: Brev A100 or multi-L4 with `nvidia-mgpu` backend
  - Use: Distributed state vector for N=40-50
  - Strategy: Circuit partitioning across GPUs using CUDA-Q's built-in distribution
  - Expected: Enable N≥47 where quantum advantage is predicted

**Implementation:**
```python
# Single GPU
cudaq.set_target("nvidia")
result = cudaq.sample(circuit, shots_count=1000)

# Multi-GPU (if available)
cudaq.set_target("nvidia-mgpu")
result = cudaq.sample(circuit, shots_count=1000)
```

### Classical Acceleration (MTS)

**Strategy:** GPU-accelerated Memetic Tabu Search using CuPy

**Key Optimizations:**

1. **Vectorized Energy Calculation:**
   ```python
   # CPU: O(N²) per sequence, serial
   def compute_energy_gpu(population):
       # Convert population to CuPy array
       pop_gpu = cp.array(population)  # Shape: (pop_size, N)

       # Vectorized computation of all C_k values
       # Compute all autocorrelations in parallel
       energies = []
       for k in range(1, N):
           C_k = cp.sum(pop_gpu[:, :-k] * pop_gpu[:, k:], axis=1)
           energies.append(C_k ** 2)

       return cp.sum(cp.array(energies), axis=0)
   ```
   Expected speedup: 50-100x for batch energy evaluation

2. **Parallel Neighbor Generation:**
   - Generate all N single-bit-flip neighbors on GPU simultaneously
   - Evaluate energies in single batched kernel call
   - Expected speedup: 20-30x for tabu search local optimization

3. **Batched Population Operations:**
   - Combine/mutate operations vectorized across population
   - Multi-parent selection and crossover in parallel
   - Expected speedup: 10-15x for population management

**Target Performance:**
- Classical CPU MTS: ~1 second per generation for N=30, pop_size=20
- GPU-accelerated MTS: ~0.05 seconds per generation (20x speedup)
- Enables scaling to larger populations (pop_size=100+) and more generations

### Hardware Targets

* **Development Environment:**
  - qBraid (CPU) for initial development, debugging, and unit testing
  - Free tier, unlimited for Phase 1

* **Testing Environment:**
  - Brev L4 (24GB VRAM) for GPU porting and validation
  - Cost: ~$0.60/hour, budget 4 hours = $2.40
  - Use for: N=20-30 testing, CuPy implementation validation

* **Production Environment:**
  - Brev L4 or A100-40GB for final benchmarks
  - Cost: L4 $0.60/hr, A100 $2-3/hr
  - Budget: 2-3 hours = $5-10 maximum
  - Use for: N=40-50 scaling analysis, final presentation results

---

## 4. The Verification Plan
**Owner:** Quality Assurance PIC

### Unit Testing Strategy

* **Framework:** pytest with comprehensive test coverage
* **Test Organization:**
  ```
  tests/
    test_energy.py          # Energy calculation correctness
    test_symmetries.py      # LABS symmetries preservation
    test_mts.py             # MTS algorithm components
    test_quantum.py         # Quantum circuit correctness
    test_integration.py     # End-to-end workflow
  ```

* **AI Hallucination Guardrails:**
  1. **Property-Based Testing:** Use Hypothesis library to generate random test cases
     - Energy must be non-negative for all sequences
     - Energy must be integer-valued
     - Symmetries must preserve energy exactly

  2. **Differential Testing:** Compare GPU vs CPU implementations
     - All CuPy energy calculations must match NumPy within 1e-10
     - Quantum circuit samples must produce valid binary sequences

  3. **Regression Testing:** Lock in known-good results
     - Store golden outputs for N=7,11,15 test cases
     - Fail any changes that break existing test cases

  4. **Code Review Gates:**
     - All AI-generated CUDA-Q kernels reviewed for gate sequence correctness
     - Cross-reference circuit implementations against paper diagrams (Figure 4)

### Core Correctness Checks

**Check 1 (Symmetry Invariance):**
```python
def test_symmetry_invariance():
    """LABS symmetries must preserve energy exactly."""
    s = np.random.choice([-1, 1], size=15)
    E_original = compute_energy(s)

    # Test all 8 symmetries
    assert compute_energy(-s) == E_original  # Flip
    assert compute_energy(s[::-1]) == E_original  # Reverse
    assert compute_energy(-s[::-1]) == E_original  # Flip + Reverse
    # ... test remaining symmetries
```

**Check 2 (Ground Truth Validation):**
```python
def test_known_optima():
    """Verify against published optimal energies."""
    known_optima = {
        7: (np.array([1, 1, 1, -1, -1, 1, -1]), 2),
        11: (optimal_seq_11, 8),
        15: (optimal_seq_15, 20),
    }

    for N, (seq, expected_energy) in known_optima.items():
        assert compute_energy(seq) == expected_energy
```

**Check 3 (Quantum Circuit Validity):**
```python
def test_quantum_samples_valid():
    """Quantum samples must be valid binary sequences."""
    samples = sample_quantum_population(N=11, pop_size=100)

    for s in samples:
        assert len(s) == 11
        assert set(s).issubset({-1, 1})
        assert not np.isnan(compute_energy(s))
```

**Check 4 (MTS Improvement):**
```python
def test_mts_improves():
    """MTS must improve over random initialization."""
    N = 15
    random_pop = [np.random.choice([-1, 1], N) for _ in range(20)]
    initial_best = min(compute_energy(s) for s in random_pop)

    _, final_best, _, _ = memetic_tabu_search(N, initial_population=random_pop)
    assert final_best <= initial_best  # Must not get worse
```

**Check 5 (GPU-CPU Consistency):**
```python
def test_gpu_cpu_match():
    """GPU and CPU implementations must agree."""
    population = [np.random.choice([-1, 1], 20) for _ in range(50)]

    # CPU reference
    energies_cpu = [compute_energy(s) for s in population]

    # GPU implementation
    energies_gpu = compute_energy_gpu(np.array(population)).get()

    np.testing.assert_allclose(energies_cpu, energies_gpu, rtol=1e-10)
```

### Continuous Validation During Development

* **Pre-commit Hook:** Run fast unit tests before every commit
* **Integration Testing:** Full workflow test after each major component
* **Benchmark Comparison:** Track performance metrics across code changes
* **Manual Review:** Visual inspection of energy convergence plots

---

## 5. Execution Strategy & Success Metrics
**Owner:** Technical Marketing PIC

### Agentic Workflow

**Tool Orchestration:**

* **IDE:** VS Code with Claude Code CLI
* **AI Assistant Usage:**
  1. **Code Generation:** Use Claude for implementing CUDA-Q kernels from paper equations
  2. **Debugging:** Paste error logs to AI for troubleshooting and refactoring
  3. **Optimization:** Request CuPy vectorization strategies for bottlenecks
  4. **Documentation:** Generate docstrings and code comments

* **Safety Protocols:**
  - Never commit AI code without unit test validation
  - Always cross-reference CUDA-Q syntax against official docs
  - QA Lead has veto power on any AI-generated changes
  - Maintain `AI_REPORT.md` documenting all AI interactions

* **Workflow Pipeline:**
  ```
  [AI Generates Code] → [QA Writes Test] → [Run Test]
       ↓ (fail)                                ↓ (pass)
  [Paste Error to AI] ← ← ← ← ← → [Code Review] → [Commit]
  ```

### Success Metrics

**Metric 1 (Approximation Quality):**
- **Target:** Quantum-seeded MTS achieves ≥10% better final energy than random-seeded MTS
- **Measurement:** Run 10 trials each for N=20,25,30 and compare mean best energies
- **Stretch Goal:** Quantum initialization provides "outlier" runs with 2x better performance

**Metric 2 (Computational Speedup):**
- **Target:** 10x total speedup over CPU-only baseline
  - Quantum simulation: 15x GPU vs CPU (CUDA-Q nvidia backend)
  - Classical MTS: 20x GPU vs CPU (CuPy vectorization)
- **Measurement:** Wall-clock time for complete QE-MTS workflow (N=30, 50 generations)
- **Stretch Goal:** 50x speedup enabling real-time interactive optimization

**Metric 3 (Scaling Capability):**
- **Target:** Successfully solve N≥35 (beyond CPU-feasible range)
- **Measurement:** Complete QE-MTS run with quantum sampling + 50 MTS generations
- **Stretch Goal:** Reach N=47 where quantum advantage is theoretically predicted

**Metric 4 (Efficiency - O(N) Scaling):**
- **Target:** Demonstrate improved empirical scaling constant
- **Measurement:** Fit exponential curve to time-to-solution data: T(N) = c × a^N
- **Goal:** Achieve a < 1.30 (better than classical O(1.34^N))

### Visualization Plan

**Plot 1: Quantum vs Random Initialization Comparison**
- X-axis: Generation number
- Y-axis: Best energy found
- Two lines: Quantum-seeded (blue), Random-seeded (red)
- Shows faster convergence and better final solutions for quantum approach

**Plot 2: Final Population Energy Distribution**
- Side-by-side histograms (or box plots)
- Left: Random initialization final population energies
- Right: Quantum initialization final population energies
- Shows quantum approach produces tighter, lower-energy distribution

**Plot 3: GPU Speedup Analysis**
- X-axis: Problem size N
- Y-axis: Speedup factor (log scale)
- Multiple lines: Quantum simulation speedup, MTS speedup, Total speedup
- Shows acceleration across problem sizes

**Plot 4: Scaling Comparison**
- X-axis: Problem size N
- Y-axis: Time to solution (log scale)
- Multiple lines: CPU baseline, GPU accelerated, Theoretical O(1.34^N), Our O(1.24^N)
- Demonstrates improved scaling behavior

**Plot 5: Energy Landscape Visualization**
- For N=11 or N=15: 2D projection of energy landscape
- Scatter points: Initial quantum samples (green), Final MTS solutions (red)
- Shows quantum samples start in better regions of solution space

---

## 6. Resource Management Plan
**Owner:** GPU Acceleration PIC

### Budget Allocation

**Total Budget:** Assume $20-30 in cloud credits

**Phase 1 - Development (qBraid, $0):**
- Duration: First 8 hours
- Activities: Complete all tutorial exercises, implement MTS, write quantum kernels
- Testing: All unit tests pass on CPU
- **No GPU costs**

**Phase 2a - GPU Porting (Brev L4, ~$3):**
- Duration: 4-5 hours @ $0.60/hour
- Activities:
  - Port CUDA-Q to nvidia backend (1 hour)
  - Implement CuPy acceleration (2 hours)
  - Debug GPU-specific issues (1-2 hours)
- **Cost: $2.40-3.00**

**Phase 2b - Benchmarking (Brev L4/A100, ~$5-10):**
- Duration: 2-3 hours @ $2-3/hour (if using A100)
- Activities:
  - Run scaling analysis N=20,25,30,35,40 (1 hour)
  - Generate all visualization plots (0.5 hours)
  - Capture demo videos and screenshots (0.5 hours)
- **Cost: $5-10**

**Emergency Reserve:** $5
- For debugging unexpected GPU issues
- Re-running failed benchmarks
- Last-minute presentation improvements

### Cost Control Strategies

1. **Develop on Free Tier:** Complete 90% of work on qBraid before touching Brev
2. **Auto-Shutdown:** Configure Brev instances to auto-shutdown after 30 min idle
3. **Manual Oversight:** GPU PIC responsible for monitoring active instances
4. **Meal Break Protocol:** Mandatory shutdown during team breaks
5. **Checkpoint Saves:** Save all results immediately, don't re-run unnecessarily
6. **Realistic Scoping:** Start with L4, only use A100 if actually needed for N>40
7. **Parallel Work:** While GPU runs, team works on presentation/documentation

### Instance Selection Guide

| Instance Type | VRAM | Cost/Hour | Best For | Max N |
|---------------|------|-----------|----------|-------|
| qBraid CPU | - | $0 | Development, testing | 20 |
| Brev L4 | 24GB | $0.60 | GPU porting, N≤35 | 35 |
| Brev A100-40GB | 40GB | $2-3 | Large N, final benchmarks | 45+ |
| Brev Multi-L4 | 48GB+ | $1.20+ | Multi-GPU testing | 50+ |

**Decision Rule:** Use cheapest instance that can hold state vector (2^N complex numbers)
- State vector size: 2^N × 16 bytes (complex128)
- N=30: 16 GB
- N=35: 512 GB (requires approximation or multi-GPU)

---

## 7. Risk Mitigation

### Technical Risks

**Risk 1: Quantum circuit too deep for GPU simulation**
- Mitigation: Start with n_steps=1 Trotter, only increase if performance allows
- Fallback: Reduce N to stay within memory limits

**Risk 2: CuPy implementation doesn't match NumPy**
- Mitigation: Comprehensive differential testing (GPU vs CPU)
- Fallback: Use NumPy + multiprocessing if GPU bugs persist

**Risk 3: Quantum advantage doesn't materialize for small N**
- Mitigation: Focus narrative on "proof of concept" and scaling trends
- Fallback: Emphasize learning outcomes and GPU acceleration wins

### Schedule Risks

**Risk 1: Phase 1 deadline (10pm tonight) too tight**
- Mitigation: Prioritize PRD and self-validation over perfect code
- Fallback: Submit working baseline, note future improvements in PRD

**Risk 2: GPU debugging takes longer than expected**
- Mitigation: Have CPU-only submission as fallback
- Fallback: Present CPU results + GPU acceleration strategy as "future work"

### Team Coordination Risks

**Risk 1: Parallel work creates merge conflicts**
- Mitigation: Clear module ownership, frequent communication
- Fallback: Project Lead manually integrates code if needed

---

## 8. Deliverables Checklist

### Phase 1 (Due: 10pm EST, Jan 31)
- [x] Completed tutorial notebook with all 6 exercises
- [x] Self-validation section with 5+ tests
- [x] PRD.md (this document)
- [ ] Commit and push to GitHub
- [ ] Verify all code runs on qBraid

### Phase 2 (Due: 10am EST, Feb 1)
- [ ] GPU-accelerated implementation (CuPy + CUDA-Q nvidia backend)
- [ ] Comprehensive test suite (tests.py)
- [ ] AI_REPORT.md documenting AI usage
- [ ] All visualization plots generated
- [ ] Presentation slides or video (5-10 min)
- [ ] Final submission to judges

---

## 9. Contact & Communication

**Primary Communication:** Discord (farzana3301, Shams Nibir)
**Backup Communication:** GitHub Issues
**Code Repository:** https://github.com/FarzanaR11/2026-NVIDIA
**Live Progress:** GitHub Repository

**Availability During Hackathon:**
- All team members available until Phase 1 deadline (10pm)
- Phase 2 work scheduled for tomorrow morning
- Team reconvenes 7am for final push to 10am deadline

---

**Document Version:** 1.0
**Last Updated:** January 31, 2026
**Next Review:** After Phase 1 submission
