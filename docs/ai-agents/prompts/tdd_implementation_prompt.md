# TDD Implementation Prompt

**Version**: 1.0.0  
**Last Updated**: 2025-07-07  
**Specialization**: Test-Driven Development

## 🎯 Objective

Implement the specified feature using strict Test-Driven Development (TDD) methodology with Red-Green-Refactor cycles.

## 📚 Required Reading

**MUST READ** before starting:
1. **Feature Requirement**: `docs/requirements/feature-specifications/[FR-XXX]*.md`
2. **TDD Workflow**: `docs/ai-agents/workflows/tdd-workflow.md`
3. **TDD Quick Reference**: `docs/ai-agents/workflows/tdd-quick-reference.md`
4. **Related ADRs**: Listed in feature requirement (especially ADR-006: Testing Strategy)
5. **Project Coding Standards**: Follow all ADR requirements for documentation, type hints, and code quality

## 🔄 TDD Process

### Phase 1: TDD Setup (30 minutes)
```bash
# Set up test infrastructure
mkdir -p tests/{unit,integration}/[feature_area]
touch tests/conftest.py

# Install test dependencies (per ADR-006)
pip install pytest pytest-cov pytest-mock hypothesis
```

**ADR Compliance Requirements:**
- All test methods MUST have Google-style docstrings (ADR-006)
- Follow comprehensive testing framework patterns (ADR-006)
- Include type hints for all test parameters and returns (ADR-005)
- Use structured logging in test utilities (ADR-007)
- Follow error handling patterns in test assertions (ADR-003)
- Use Click testing utilities for CLI component testing (ADR-004)
- Test plugin interfaces with proper type safety (ADR-002)
- Follow Operation Strategy Pattern in all operation tests (ADR-001)

### Phase 2: Red-Green-Refactor Cycles
**Follow strict TDD discipline**: 🔴 RED → 🟢 GREEN → 🔵 REFACTOR

#### Cycle Guidelines:
- **🔴 RED (2-5 min)**: Write ONE failing test
- **🟢 GREEN (5-10 min)**: Write MINIMAL code to pass
- **🔵 REFACTOR (2-5 min)**: Improve while keeping tests green
- **Total cycle**: 10-20 minutes maximum

#### ✅ Cycle Completion:
**After each successful cycle**:
1. Remove TDD phase markers (🔴🟢🔵) from comments
2. Add Google-style docstrings to all test methods (ADR-006)
3. Add type hints to all test parameters and returns (ADR-005)
4. Clean up temporary/debug code
5. Ensure all tests pass
6. Update documentation if needed

#### TDD Commands:
```bash
# Run single test (RED phase)
pytest tests/unit/test_[feature].py::test_specific_test -v

# Run all feature tests (GREEN/REFACTOR phases)  
pytest tests/unit/test_[feature].py -v

# Run with coverage
pytest tests/unit/ --cov=src/[module] --cov-report=term-missing

# CLI component testing (when testing CLI features)
pytest tests/unit/cli/ -v --tb=short

# Plugin testing (when testing plugin interfaces)
pytest tests/unit/plugins/ -v --tb=short
```

### Phase 3: Integration TDD (30-45 minutes)
Apply TDD to integration testing:
- 🔴 Write failing integration test
- 🟢 Make integration work
- 🔵 Refactor integration code

## ✅ TDD Quality Gates

**After each cycle**:
- [ ] All tests pass ✅
- [ ] No regressions ✅  
- [ ] Coverage increases ✅
- [ ] Tests run fast (< 30 seconds) ✅
- [ ] All test methods have Google-style docstrings ✅
- [ ] Type hints added per ADR-005 ✅

**After feature completion**:
- [ ] 95%+ test coverage (ADR-006 requirement)
- [ ] All acceptance criteria met through tests
- [ ] Integration tests pass
- [ ] Performance requirements met
- [ ] All ADR compliance requirements satisfied
- [ ] Test documentation follows project standards
- [ ] CLI tests use Click testing utilities (when applicable)
- [ ] Plugin interface tests verify type safety (when applicable)
- [ ] Logging behavior properly tested in test utilities

## 🚨 TDD Discipline

### ❌ TDD Anti-Patterns
- Writing multiple tests before making any pass
- Writing implementation before tests
- Skipping the refactor phase
- Making tests too complex

### ✅ TDD Best Practices  
- One test at a time
- Simplest code to make test pass
- Refactor when tests are green
- Test behavior, not implementation
- **Google-style docstrings for all test methods (ADR-006)**
- **Complete type annotations (ADR-005)**
- **Comprehensive error handling coverage (ADR-003)**
- **Follow testing framework patterns from ADR-006**
- **Use Click testing utilities for CLI components (ADR-004)**
- **Validate plugin interfaces with type safety (ADR-002)**
- **Test logging behavior in utilities (ADR-007)**


## 🎯 Success Criteria

- [ ] All TDD cycles completed successfully
- [ ] All acceptance criteria met through tests
- [ ] High test coverage achieved naturally (≥95% per ADR-006)
- [ ] Code emerged from tests (not written first)
- [ ] **All test methods have Google-style docstrings**
- [ ] **Complete type annotations throughout**
- [ ] **ADR compliance verified and documented**
- [ ] **Test framework patterns from ADR-006 implemented**
- [ ] **CLI components tested with Click utilities (if applicable)**
- [ ] **Plugin interfaces tested for type safety (if applicable)**
- [ ] **Logging behavior validated in test utilities**

---

**Key TDD Principle**: Let tests drive the implementation. Don't write code unless you have a failing test that requires it.

