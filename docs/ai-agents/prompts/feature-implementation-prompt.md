# Feature Implementation Prompt

**Version**: 1.0.0  

## 🎯 Objective

Implement the specified feature requirement following established project patterns and achieving all acceptance criteria.

## 📚 Required Reading (Complete Before Implementation)

**CRITICAL**: You MUST read these documents in this exact order:

1. **Feature Requirement**: `docs/requirements/feature-specifications/[FR-XXX]*.md`
2. **Implementation Methodology**: 
   - `docs/ai-agents/workflows/tdd-workflow.md` (recommended for complex features)
   - `docs/ai-agents/workflows/development-workflow.md` (for simple features)
3. **Project Context**: `docs/project-overview.md`
4. **Quality Standards**: `docs/coding-standards.md`
5. **Related ADRs**: Specified in the feature requirement

## 🛠️ Implementation Process

### Choose Your Approach
Based on feature complexity:

**Complex Features** (core functionality, many edge cases, performance critical):
```bash
Follow: docs/ai-agents/workflows/tdd-workflow.md
Use: docs/ai-agents/workflows/tdd-quick-reference.md
```

**Simple Features** (configuration, basic integrations, documentation):
```bash
Follow: docs/ai-agents/workflows/development-workflow.md
```

### Implementation Steps
1. **Read Documentation**: Complete required reading above
2. **Follow Chosen Workflow**: Execute workflow step-by-step
3. **Use Project Resources**:
   - **Templates**: Start with appropriate template from `templates/`
   - **Examples**: Reference similar implementations in `examples/`
   - **Patterns**: Follow ADR patterns specified in feature requirement

## ✅ Validation Commands

Run these commands to validate your implementation:

```bash
# Quality gates (must all pass)
make quality-check  # or individual commands from CODING_STANDARDS.md

# Test validation  
pytest tests/ --cov=src --cov-fail-under=95

# Feature validation
# [Specific validation commands from feature requirement]
```

## 🚀 Completion Checklist

- [ ] All acceptance criteria from feature requirement are met
- [ ] All quality gates pass (see `docs/CODING_STANDARDS.md`)
- [ ] Integration tests pass
- [ ] Documentation updated (as specified in workflow)
- [ ] Ready for PR using `.github/PULL_REQUEST_TEMPLATE.md`

## 📝 Quick Reference

### When Stuck
- **Patterns**: Check `examples/` directory for similar implementations
- **Architecture**: Review relevant ADRs for architectural guidance  
- **Quality**: Reference `docs/CODING_STANDARDS.md` for specific requirements
- **Testing**: Use patterns from `examples/test_example.py`
- **Troubleshooting**: See `docs/ai-agents/guidelines/troubleshooting.md`

### Key Principle
**Follow existing patterns**: This project has established patterns for everything. Don't invent new approaches - use what's already documented and proven.

---

**Remember**: Quality is more important than speed. Take time to read the documentation and follow established patterns. 
