# Contributing to this project

## Before Contributing

1. **Read Relevant ADRs**: Check `/docs/adr/` for architectural decisions that affect your work
2. **Follow Established Patterns**: Use the patterns documented in ADRs
3. **Update ADRs**: If your contribution changes architectural decisions, update or create new ADRs

## Quick Start for AI Agents

When generating code for this project, always:
1. Check `examples/` directory for patterns
2. Use templates from `templates/` directory
3. Follow the architecture in `docs/architecture.md`
4. Implement comprehensive tests
5. Add proper type hints and docstrings

## Development Workflow

### Setting Up Development Environment


### Branch Strategy

```
main                    # Production-ready code
├── develop            # Integration branch
├── feature/add-power  # Feature branches
├── hotfix/div-zero    # Critical fixes
└── release/v1.1.0     # Release preparation
```

**Branch Naming:**
- `feature/short-description`
- `bugfix/issue-description`
- `hotfix/critical-fix`
- `docs/documentation-update`

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(core): add power operation support
fix(cli): handle division by zero gracefully
docs(api): update operation interface documentation
test(core): add edge cases for multiplication
```

### Development Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Implement Changes**
   - Follow coding standards in `CODING_STANDARDS.md`
   - Use patterns from `examples/` directory
   - Write tests first (TDD approach)
   - Add comprehensive docstrings

3. **Test Your Changes**
   ```bash
   make test              # Run all tests
   make test-coverage     # Check coverage
   make lint              # Run linting
   make type-check        # Run type checking
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat(core): add your feature"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use the PR template
   - Link related issues
   - Request appropriate reviewers

## Code Implementation Guidelines


### Error Handling Patterns

**Always use specific exceptions:**


**Include context in error messages:**

## Testing Guidelines

### Testing Strategy

The Story Curator follows a **strict two-tier testing approach**. For complete details, see [ADR-006: Testing Strategy](adr/ADR-006-testing-strategy.md).

#### Quick Summary
- **Unit Tests (`tests_unit/`)**: Mock all dependencies for fast, isolated testing
- **Integration Tests (`tests_integration/`)**: Real components for end-to-end validation

#### Test Commands
```bash
# Unit tests (fast development feedback)
pytest src/component/tests_unit/ -v

# Integration tests (real component validation) 
pytest src/component/tests_integration/ -v
```

### Test Categories
- **Unit Tests**: Test individual classes/methods in isolation with mocks
- **Integration Tests**: Test component interactions with real dependencies
- **End-to-End Tests**: Test complete workflows with real audio and database
- **Performance Tests**: Benchmark critical operations with real components
- **Security Tests**: Test input validation and error handling

## Code Review Guidelines

### For Reviewers
- Check adherence to coding standards
- Verify comprehensive test coverage
- Ensure proper error handling
- Review documentation completeness
- Test the changes locally

### Pull Request Requirements
- [ ] All tests pass
- [ ] Coverage remains above 95%
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Breaking changes documented

### Code Review Checklist
- [ ] Code follows established patterns
- [ ] Proper error handling implemented
- [ ] Comprehensive tests included
- [ ] Documentation is clear and complete
- [ ] No security vulnerabilities
- [ ] Performance impact considered

## AI Agent Integration

### Best Practices for AI Code Generation

**When asking AI agents to generate code:**

1. **Reference existing patterns:**
   ```
   "Create a new operation following the pattern in examples/operation_example.py"
   ```

2. **Specify the template to use:**
   ```
   "Use templates/operation_template.py as the starting point"
   ```

3. **Include context:**
   ```
   "Add a logarithm operation that integrates with our existing registry system"
   ```

4. **Request complete implementation:**
   ```
   "Include the operation class, tests, registration, and CLI integration"
   ```

### AI Agent Guidelines

When implementing new features:
1. Check `docs/adr/` for relevant architectural decisions
2. Follow the patterns shown in ADR examples
3. Reference specific ADRs in code comments when implementing their patterns

## Release Process

### Version Numbering
We follow Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Release Steps
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Create and test distribution packages
6. Merge to main
7. Tag release
8. Deploy to PyPI

## Getting Help

- **Documentation Issues**: Create issue with `docs` label
- **Bug Reports**: Use bug report template
- **Feature Requests**: Use feature request template
- **Development Questions**: Tag maintainers in issues

## Additional Resources

- [Project Overview](PROJECT_OVERVIEW.md) - Complete project context
- [Architecture Guide](docs/architecture.md) - System design details
- [API Reference](docs/API_REFERENCE.md) - Interface documentation
- [Coding Standards](CODING_STANDARDS.md) - Detailed style guide
- [Examples Directory](examples/) - Code pattern examples
- [Templates Directory](templates/) - Boilerplate code

---

**Remember**: Good contributions make the codebase better for everyone, including AI agents that help with future development!
