# Agent Coding Steps

This document defines optimized steps for an AI agent to develop code using test-driven development (TDD). The agent implements one focused use case per iteration, with clear validation checkpoints and improved error handling.

## Key Improvements
- **Clear Success/Failure Criteria**: Each step has explicit validation
- **Agent-Friendly Instructions**: More specific, actionable guidance
- **Better Error Recovery**: Structured fallback strategies
- **Clearer Boundaries**: When to halt vs. continue vs. seek clarification
- **Improved Logging**: More structured and actionable log entries

## Required Files
- `{design_doc}`: Feature design document (e.g., `docs/feature1-design.md`)
- `{use_cases_doc}` (optional): Separate use cases document (e.g., `docs/feature1-use-cases.md`)
- `{test_plan_doc}`: Test plan with test cases (e.g., `docs/feature1-test-plan.md`)

## Supporting Files (Must Exist)
- `docs/coding-standards.md`: Language, framework, patterns, naming conventions
- `docs/testing-standards.md`: Testing framework, coverage requirements, test structure
- `docs/environment-setup.md`: Development environment configuration
- `docs/notes.md`: User insights and clarifications log
- `docs/logs.md`: Process log for errors, progress, and proposals

## Execution Prompt
```
Execute the steps in `docs/agent-coding-steps.md` with:
- Design: `{design_doc}`
- Use Cases: `{use_cases_doc}` (if separate)
- Test Plan: `{test_plan_doc}`
```

## Development Steps

### Phase 1: Validation & Setup

**1. File Validation**
- Check existence of required files: `{design_doc}`, `{test_plan_doc}`, and `{use_cases_doc}` (if specified)
- **Success**: All required files exist and are readable
- **Failure**: Log missing files to `docs/logs.md` with format: `[YYYY-MM-DD] CRITICAL: Missing required file: {filename}` and HALT
- **Action**: Read file headers/first sections to validate they contain expected content types

**2. User Insights Review**
- Read `docs/notes.md` for previous insights, constraints, and preferences
- **Success**: File processed (even if empty)
- **Failure**: Create empty `docs/notes.md` if missing
- **Log**: `[YYYY-MM-DD] SETUP: Reviewed {X} previous insights from notes.md`

**3. Environment Verification**
- Verify development environment per `docs/environment-setup.md`
- Check for required tools, dependencies, test runners
- **Success**: Environment ready for development
- **Failure**: Log specific missing components and HALT
- **Log**: `[YYYY-MM-DD] SETUP: Environment validated - {tool_list}`

### Phase 2: Document Analysis

**4. Design Document Analysis**
- Extract: feature scope, requirements, technical constraints, architecture decisions
- Identify: main components, interfaces, data structures
- **Success**: Clear understanding of feature boundaries and technical approach
- **Failure**: If design is unclear, log specific ambiguities and request clarification
- **Log**: `[YYYY-MM-DD] ANALYSIS: Feature scope - {brief_summary}`

**5. Use Case Extraction**
- If `{use_cases_doc}` exists: Parse structured use cases
- Else: Extract from `{design_doc}` (look for sections: "Use Cases", "User Stories", "Scenarios", "Examples")
- **Required Format**: Each use case should have: name, description, inputs, expected outputs, preconditions
- **Success**: At least one well-defined use case identified
- **Failure**: If no clear use cases found, log issue and HALT for clarification
- **Log**: `[YYYY-MM-DD] ANALYSIS: Found {X} use cases: {use_case_names}`

**6. Test Plan Validation**
- Map test cases to use cases from step 5
- Verify coverage: positive cases, negative cases, edge cases, error conditions
- **Success**: Each use case has corresponding test cases
- **Failure**: Log gaps in test coverage and propose additions
- **Log**: `[YYYY-MM-DD] ANALYSIS: Test coverage - {X} test cases for {Y} use cases`

**7. Document Consistency Check**
- Cross-reference design, use cases, and test plan for alignment
- **Success**: No major inconsistencies found
- **Inconsistency Found**: Log discrepancies and propose resolutions to `docs/logs.md`
- **Format**: `[YYYY-MM-DD] PROPOSAL: Design inconsistency - {description} - Suggested fix: {solution}`

### Phase 3: Implementation Planning

**8. Codebase Analysis**
- Scan existing code for: related functionality, potential conflicts, integration points
- Identify: entry points, existing test structure, dependencies
- **Success**: Clear understanding of where new code fits
- **Failure**: If codebase structure is unclear, request guidance
- **Log**: `[YYYY-MM-DD] CODEBASE: Analysis complete - Integration points: {list}`

**9. Use Case Prioritization**
- Select next use case based on: dependencies, complexity, risk
- Prioritize: foundational cases first, then dependent cases
- **Success**: One specific use case selected for implementation
- **Log**: `[YYYY-MM-DD] PLANNING: Selected use case '{use_case_name}' - Rationale: {reason}`

**10. Complexity Assessment**
- Evaluate selected use case: number of test cases, code changes, dependencies
- **Simple**: ≤5 test cases, ≤50 lines of code, no new dependencies
- **Complex**: >5 test cases OR >50 lines of code OR new dependencies
- **If Complex**: Propose breaking into sub-use cases and HALT for approval
- **Log**: `[YYYY-MM-DD] COMPLEXITY: Use case '{name}' assessed as {simple/complex} - {justification}`

**11. Clarification Check**
- Review use case for ambiguities in: inputs, outputs, behavior, error handling
- **Clear**: Proceed to implementation
- **Ambiguous**: List specific questions and HALT for user input
- **Log**: `[YYYY-MM-DD] CLARIFICATION: {number} questions about '{use_case_name}'`

### Phase 4: TDD Implementation

**12. Test Creation**
- Write unit tests covering all test cases for the selected use case
- Follow `docs/testing-standards.md` for: framework, naming, structure, assertions
- Include: setup, positive tests, negative tests, edge cases, cleanup
- **Success**: All test cases have corresponding unit tests, tests fail initially (red phase)
- **Failure**: If test framework issues, log and request help
- **Log**: `[YYYY-MM-DD] TESTS: Created {X} unit tests for '{use_case_name}'`

**13. Static Analysis (Pre-Implementation)**
- Run linting and formatting on test files
- **Success**: Tests pass static analysis
- **Failure**: Fix automatically if possible, otherwise log issues
- **Log**: `[YYYY-MM-DD] STATIC: Test files pass linting`

**14. Code Implementation**
- Implement minimum code to make tests pass (green phase)
- Follow `docs/coding-standards.md` for: style, patterns, naming, documentation
- Focus on: making tests pass, not over-engineering
- **Success**: Implementation makes tests pass without breaking existing functionality
- **Log**: `[YYYY-MM-DD] CODE: Implemented '{use_case_name}' - {lines_changed} lines`

**15. Test Execution**
- Run all tests (new + existing) to ensure no regressions
- Use test runner specified in `docs/testing-standards.md`
- **Success**: All tests pass
- **Failure**: Record specific failures and attempt fixes (max 3 iterations)
- **Log**: `[YYYY-MM-DD] TESTING: {passed}/{total} tests pass`

**16. Failure Resolution**
- If tests fail, analyze and fix (max 3 attempts)
- **Iteration 1-3**: Fix code, re-run tests, log attempts
- **After 3 failures**: Log as blocker and HALT for assistance
- **Log**: `[YYYY-MM-DD] BLOCKER: Unresolved test failures after 3 attempts - {failure_summary}`

**17. Code Refactoring (Optional)**
- If tests pass, refactor for clarity/efficiency (refactor phase)
- Maintain: same test results, coding standards compliance
- **Success**: Refactored code passes all tests
- **Skip**: If code is already clean or time-constrained
- **Log**: `[YYYY-MM-DD] REFACTOR: {description_of_changes}`

### Phase 5: Finalization

**18. Final Static Analysis**
- Run complete linting, formatting, and any additional code quality checks
- **Success**: All code passes quality gates
- **Failure**: Fix issues or log as blockers
- **Log**: `[YYYY-MM-DD] QUALITY: Final code quality check passed`

**19. Documentation Updates**
- Propose updates to design/use case/test plan documents based on implementation learnings
- **Format**: `[YYYY-MM-DD] DOC_PROPOSAL: {document_name} - {section} - {proposed_change} - Reason: {justification}`
- **Log**: All proposals to `docs/logs.md`

**20. Insights Capture**
- Document any new insights, edge cases, or constraints discovered during implementation
- **Add to `docs/notes.md`**: `[YYYY-MM-DD] {feature_name}: {insight_description}`
- **Examples**: Performance considerations, integration gotchas, user feedback
- **Log**: `[YYYY-MM-DD] INSIGHTS: Captured {X} new insights`

**21. Completion Summary**
- Provide summary: use case implemented, tests added, files changed
- **Success Criteria**: All tests pass, code follows standards, documentation updated
- **Next Steps**: Suggest next use case or indicate completion
- **Log**: `[YYYY-MM-DD] COMPLETE: Use case '{name}' implemented successfully`

## Agent Guidelines

### When to HALT
- Missing required files
- Unresolvable document inconsistencies
- Complex use cases needing decomposition
- Ambiguous requirements needing clarification
- Unresolved test failures after 3 attempts
- Environment setup failures

### When to Continue
- Minor documentation gaps (propose fixes)
- Simple refactoring opportunities
- Optional optimizations
- Non-critical warnings

### Log Entry Standards
```
[YYYY-MM-DD] {CATEGORY}: {Description}
Categories: SETUP, ANALYSIS, PLANNING, TESTS, CODE, TESTING, REFACTOR, QUALITY, BLOCKER, COMPLETE, PROPOSAL, INSIGHTS
```

### Error Recovery
1. **File Issues**: Check alternate locations, create if reasonable
2. **Test Failures**: Analyze error messages, check dependencies, verify environment
3. **Code Issues**: Review coding standards, check for typos, validate logic
4. **Integration Issues**: Verify interfaces, check for breaking changes

## Success Metrics
- **Code Quality**: All tests pass, linting clean, standards compliance
- **Documentation**: Clear logs, actionable proposals, captured insights
- **Iterative Progress**: One use case completed per cycle
- **Developer Efficiency**: Clear status, minimal clarification needed
