# Story Curator

The project is a curator and analyzer of children's stories, using documentation-first, test-driven, agent-supervised development. This project was developed using Microsoft Visual Studio Code, assisted by GitHub Copilot with Claude Sonnet 4 as the underlying model.

## Project Overview

For a detailed description of the application, its architecture, features, and development standards, see the [Project Overview](PROJECT_OVERVIEW.md) and [Architecture Documentation](docs/architecture.md).

Key principles used for developing this project:
- **Documentation-first:** All requirements, design docs, and test plans are created and validated before coding begins.
- **Test-driven development:** Tests are written before or alongside code, ensuring correctness and rapid feedback.
- **Agent supervision:** Developers guide, review, and validate AI-generated outputs.
- **Continuous improvement:** Feedback loops and clear documentation support onboarding, compliance, and quality.

## Project Structure

- `src/` — Source code
- `tests/` — Test cases for all features
- `docs/` — Design docs, test plans, and agentic workflow guides
  - `architecture.md` — Architecture documentation
  - `technical_decisions.md` — Detailed explanation of technology choices
  - `coding-standards.md` — Coding standards for all code and documentation
  - `agent-coding-steps.md` — Step-by-step guide for agentic development (see below)
  - `project-overview.md` — Detailed project architecture and standards

## Resources

- [docs/project-overview.md](project-overview.md) — Application architecture and standards
- [docs/architecture.md](docs/architecture.md) — Architecture documentation
- [docs/technical_decisions.md](docs/technical_decisions.md) — Library choices and rationale
- [docs/agent-coding-steps.md](docs/agent-coding-steps.md) — Practical guide for agentic workflows
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
