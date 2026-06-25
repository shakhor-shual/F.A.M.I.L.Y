---
name: model-evaluation-workflow
description: Evaluate model performance on local hardware — measure speed, assess reasoning coherence, check multilingual capability, identify internal conflicts (e.g., MoE expert interference), and propose alternatives (dense vs MoE, larger vs smaller).
---

# Model Evaluation Workflow

Use this skill when the user wants to evaluate, compare, or select a local LLM for their hardware. Covers end-to-end assessment from speed benchmarks to architectural fitness.

## When to Use
- User asks "which model should I run?"
- User reports slow generation, garbled output, or poor multilingual performance
- User is deciding between dense vs MoE, or different model sizes
- User has run baseline tests and needs interpretation
- User complains about expert conflict, chain-of-thought breakdown, or language mixing

## Steps

### 1. Measure Inference Speed
- Ask for tokens/sec on the target hardware (GPU model, VRAM, quantization level)
- Compare against known baselines: Pascal GPUs (P104/P40) ~50 tok/s for small models; ~12-14 tok/s for 27B models
- Flag if speed is below usable threshold for conversational use (~8 tok/s minimum for tolerable dialogue)

### 2. Assess Multilingual Capability
- Test the model on a short prompt in Russian, Chinese, and English (e.g., "Расскажи о себе" / "介绍一下你自己" / "Tell me about yourself")
- Check whether output language matches the prompt language
- If the model consistently falls back to English, flag as poor multilingual support
- For the user's use case (Russian primary, English/Chinese secondary), recommend models with proven multilingual training (Qwen 2.5, DeepSeek)

### 3. Evaluate Chain-of-Thought Coherence
- Give a multi-step reasoning task (e.g., "If I have 3 apples and give away 2, then buy 5 more, how many do I have? Explain step by step.")
- Check whether the model follows logical steps without contradicting itself
- For MoE models: look for signs of **expert conflict** — sudden topic switches, self-correction mid-response, contradictory statements in adjacent sentences
- Document any occurrences of expert conflict as a disqualifying factor for MoE

### 4. Identify Internal Architecture Conflicts
- Run the same prompt twice and compare responses for consistency
- If using an MoE model with many small experts, test with a long chain-of-thought prompt (200+ tokens) to stress expert routing
- Signs of conflict: model starts one reasoning path, abandons it, starts another; uses different "personalities" mid-response; loses track of the original question
- **Decision rule**: if expert conflict appears, advise switching to a dense model (e.g., Qwen 2.5 32B) which eliminates routing interference

### 5. Propose Alternatives
- If current model is unsuitable, recommend in this priority order:
  1. **Dense model 7B-14B fine-tuned on dialogues** — best balance for the user's hardware (Pascal GPUs)
  2. **Dense model 32B** (e.g., Qwen 2.5 32B) — if user can tolerate lower speed for higher quality
  3. **DeepSeek V2 Flash** — if cloud API is acceptable (best cost-quality balance per user's preference)
- Avoid recommending Gemma (user distrusts Google's training quality)
- Avoid recommending homemade MoE with explicit experts (proven overkill from baseline tests)

## Output Format

Provide a concise evaluation report with:
- **Model tested**: name, size, quantization
- **Hardware**: GPU, VRAM, tokens/sec
- **Multilingual**: pass/fail per language
- **Coherence**: pass/fail with evidence
- **Architecture issues**: expert conflict detected? yes/no
- **Recommendation**: dense vs MoE, specific model name, and rationale

## Examples

**User**: "I tried Dance Quen 3.5 27B on my P40. It runs at 13 tok/s but sometimes switches to English mid-Russian sentence."

**Evaluation**:
- Model: Dance Quen 3.5 27B
- Hardware: P40 (Pascal), ~13 tok/s — acceptable
- Multilingual: **fail** — Russian-to-English language drift detected
- Coherence: marginal — occasional topic shifts but no expert conflict (dense model)
- Architecture: dense — no MoE issues
- Recommendation: try Qwen 2.5 32B (dense, stronger multilingual) at lower quantization (4-bit) to fit P40 VRAM, expected ~8-10 tok/s. If speed is too low, fall back to Qwen 2.5 14B.

**User**: "My MoE with 35 experts starts talking about apples in the middle of a question about physics."

**Evaluation**:
- Model: custom MoE, 35 experts
- Hardware: unknown, likely GPU-bound
- Multilingual: not tested
- Coherence: **fail** — clear expert conflict (abrupt topic switch)
- Architecture: MoE — expert interference detected
- Recommendation: switch to a dense model immediately. MoE with many small experts causes routing conflicts during chain-of-thought. Recommended: Qwen 2.5 14B dense (fits Pascal GPUs, good multilingual, no expert conflict).