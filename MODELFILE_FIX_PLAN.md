# Plan: Fix Broken Ollama Model Templates for Tool Calling

## Problem Summary

Based on our analysis, certain Llama models (specifically `llama32-tools:latest`) generate tool calls in `<tool_call>` XML format but the Ollama server doesn't parse them into structured `tool_calls` in the API response. This causes agno (and our agent framework) to receive them as plain text content instead of executable tool calls.

**Working models:** `llama3.1:8b`, `qwen3:*` variants
**Broken models:** `llama32-tools:latest`, potentially others

## Root Cause

The issue is at the **modelfile TEMPLATE level**. The broken models have templates that:
1. Output tool calls as `<tool_call>` XML tags in message content
2. But the format doesn't match what Ollama's response parser expects
3. So Ollama doesn't extract them into the `tool_calls` response field

Working models use templates that Ollama properly recognizes and parses.

## Solution Strategy

Create corrected modelfiles for broken models by:
1. Using working model templates as reference
2. Adapting them for Llama architecture
3. Creating new custom models with `-tools-fixed` suffix

## Step-by-Step Plan

### Phase 1: Analysis (Before Running Tests)

**Goal:** Understand what makes working models work

1. ✅ **Extract and compare modelfiles** (already done):
   - `llama32-tools:latest` - BROKEN
   - `llama3.1:8b` - WORKING
   - `qwen3:8b` - WORKING

2. **Key differences identified:**
   - Llama 3.1 uses native tool call format that Ollama parses
   - Qwen uses `<tool_call>` with proper structure
   - Llama32-tools uses `<tool_call>` but parser doesn't recognize it

### Phase 2: Test Suite Execution

**Goal:** Get empirical data on all models

```bash
source .venv/bin/activate
python test_tool_calling.py
```

**Expected outputs:**
- `tool_calling_report.json` - Full data
- `tool_calling_report.md` - Human-readable summary

**This will tell us:**
- Which models are broken
- Which models work
- Performance characteristics of each

### Phase 3: Create Fixed Modelfiles

**Goal:** Build corrected models based on working templates

#### 3.1 Create Template for Llama Models

Use the working `llama3.1:8b` template as base, or adapt the `llama32-tools` template to match what Ollama expects.

**Strategy Options:**

**Option A: Copy llama3.1 template to llama32-tools**
```bash
# Extract llama3.1 template
ollama show llama3.1:8b --modelfile > llama31-template.txt

# Create new modelfile for llama32-tools using llama3.1 template
cat > llama32-tools-fixed.modelfile << 'EOF'
FROM llama32-tools:latest

# [Insert llama3.1 TEMPLATE here]
TEMPLATE """..."""

# Keep original parameters
PARAMETER repeat_penalty 1.05
PARAMETER stop <|start_header_id|>
PARAMETER stop <|end_header_id|>
PARAMETER stop <|eot_id|>
PARAMETER temperature 0.2
PARAMETER top_k 40
PARAMETER top_p 0.9
EOF

# Create the fixed model
ollama create llama32-tools-fixed -f llama32-tools-fixed.modelfile
```

**Option B: Adapt llama32-tools template to proper format**
- Analyze why parser doesn't recognize current format
- Modify TEMPLATE to match Ollama's expectations
- Test incrementally

#### 3.2 Create Fixed Models for All Broken Models

For each broken model found in Phase 2:

```bash
# Generic pattern:
ollama show <broken-model> --modelfile > original.txt
# Modify template to use working pattern
# Create fixed version
ollama create <model-name>-fixed -f fixed.modelfile
```

### Phase 4: Validation

**Goal:** Verify fixes work

1. **Add fixed models to test suite:**
```python
TEXT_MODELS = [
    # Original broken models
    "llama32-tools:latest",

    # Fixed versions
    "llama32-tools-fixed",

    # ... etc
]
```

2. **Run test suite again:**
```bash
python test_tool_calling.py
```

3. **Compare results:**
   - Fixed models should show `WORKING` status
   - Tool calls should be properly detected and parsed
   - No unparsed `<tool_call>` in content

### Phase 5: Documentation & Deployment

1. **Document the fixes:**
   - Create `MODELFILE_TEMPLATES.md` with:
     - Working template patterns
     - Common pitfalls
     - How to fix broken models

2. **Update agent configuration:**
   - Update `model_contexts.py` to use fixed models
   - Add notes about which models need fixes

3. **Create helper script:**
```python
# scripts/fix_ollama_model.py
"""Helper script to create fixed versions of broken models"""

def create_fixed_model(source_model: str, template_source: str):
    """Create a fixed version of a model with corrected template"""
    # Extract base model
    # Apply working template
    # Create new model
    pass
```

## Technical Details

### What Makes a Template Work?

Based on our analysis, working templates must:

1. **Proper tool call structure** in TEMPLATE that Ollama recognizes
2. **Correct role mappings** (system, user, assistant, tool)
3. **Tool response handling** that parser can extract
4. **Stop tokens** appropriate for the model architecture

### Template Pattern (from llama3.1:8b - WORKING)

```
{{- if eq .Role "assistant" }}<|start_header_id|>assistant<|end_header_id|>
{{- if .ToolCalls }}
{{ range .ToolCalls }}
{"name": "{{ .Function.Name }}", "parameters": {{ .Function.Arguments }}}
{{ end }}
{{- else }}
{{ .Content }}
{{- end }}{{ if not $last }}<|eot_id|>{{ end }}
```

Key: Uses `{{- if .ToolCalls }}` which suggests Ollama populates this from the model's output parsing.

### Template Pattern (from qwen3:8b - WORKING)

```
{{- else if eq .Role "assistant" }}<|im_start|>assistant
{{ if .Content }}{{ .Content }}
{{- else if .ToolCalls }}<tool_call>
{{ range .ToolCalls }}{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}
{{ end }}</tool_call>
```

Key: Uses `<tool_call>` XML tags with proper structure.

### Template Pattern (from llama32-tools:latest - BROKEN)

```
{{- else if eq $msg.Role "assistant" -}}
<|start_header_id|>assistant<|end_header_id|>
{{- if $msg.ToolCalls -}}
{{- range $tc := $msg.ToolCalls -}}
<tool_call>
{"name":"{{ $tc.Function.Name }}","arguments":{{ $tc.Function.Arguments }}}
</tool_call>
{{- end -}}
```

Key: Similar structure but parser doesn't recognize it - might be subtle formatting differences.

## Risk Assessment

### Low Risk
- Creating new models with `-fixed` suffix doesn't affect existing models
- Can test thoroughly before switching production

### Medium Risk
- Models might behave differently with new templates
- Need to validate responses are still accurate
- Token usage might change

### Mitigation
- Keep original models
- Extensive testing with test suite
- Gradual rollout (test → dev → prod)

## Success Criteria

A fixed model is considered successful when:

1. ✅ Tool calls are detected (not in content)
2. ✅ Tool calls are parseable (structured format)
3. ✅ Tools execute correctly
4. ✅ No double-call issues introduced
5. ✅ Response quality maintained
6. ✅ Performance acceptable (tokens, speed)

## Questions to Research Later

**Q: Why is unsloth qwen4b working in production?**

Possible reasons:
1. It might already have a working template
2. Different quantization might affect parsing
3. Base model architecture differences
4. Specific fine-tuning for tool calling

**Action:** Add this to Phase 2 test suite - will show us empirically if it works.

## Timeline Estimate

- **Phase 1:** Complete (already done)
- **Phase 2:** 30-60 min (test all 14 models)
- **Phase 3:** 1-2 hours (create and test fixed modelfiles)
- **Phase 4:** 30 min (validation testing)
- **Phase 5:** 30 min (documentation)

**Total:** ~3-4 hours

## Next Steps

1. ✅ Complete test suite code (done)
2. ✅ Add token counts to reports (done)
3. **RUN THE TEST SUITE** ← You are here
4. Analyze results
5. Create fixed modelfiles
6. Validate fixes
7. Deploy to production

---

## Notes

- Keep this document updated as we learn more
- Add actual test results to inform Phase 3
- Document any surprises or edge cases discovered
