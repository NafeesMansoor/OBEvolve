# Universal Code Refactoring & Engineering Protocol

## 0. Purpose

This document defines the mandatory engineering protocol for inspecting, refactoring, improving, testing, and maintaining this project.

The objective is NOT simply to make the code "cleaner".

The objective is to make the entire project:

- More correct
- More maintainable
- More reliable
- More readable
- More modular
- More testable
- More secure
- More performant where appropriate
- Easier to extend
- Easier to debug
- Easier for humans and AI agents to understand
- Less fragile
- Less dependent on accidental behavior

This protocol is intentionally project-agnostic.

It must be adapted to the actual architecture, language, framework, dependencies, deployment model, and constraints of the repository.

---

# 1. Core Principles

## 1.1 Understand Before Changing

NEVER begin by modifying code simply because something looks wrong.

First understand:

1. What the project does
2. How it is structured
3. How it starts
4. How data flows through it
5. How modules interact
6. Where state is stored
7. How configuration works
8. How external services are used
9. How background jobs work
10. How errors are handled
11. How tests work
12. How the application is deployed
13. What recent changes may have introduced problems

Do not refactor blindly.

---

## 1.2 Preserve Intended Behavior

Unless explicitly requested otherwise:

> Refactoring must preserve externally observable behavior.

Do not change business rules, API contracts, database semantics, user workflows, authentication behavior, authorization rules, file formats, configuration semantics, CLI behavior, output formats, or existing integrations unless the change is intentional, documented, and tested.

---

## 1.3 Fix Root Causes, Not Symptoms

When encountering a problem:

DO NOT immediately patch the visible error.

Determine:

- Why it occurs
- Where it originates
- Why existing safeguards failed
- Whether similar problems exist elsewhere
- Whether the architecture encourages the problem

Prefer:

    Root cause → architectural improvement → targeted fix → regression test

over:

    Error → quick patch → new hidden problem

---

## 1.4 Small, Verifiable Changes

Refactoring should be incremental.

Prefer:

    Inspect
    ↓
    Plan
    ↓
    Change one logical area
    ↓
    Validate
    ↓
    Continue

Avoid:

    Inspect
    ↓
    Rewrite half the repository
    ↓
    Hope everything still works

---

# 2. Mandatory Repository Reconnaissance

Before making significant changes, inspect the repository.

## 2.1 Identify

Determine:

- Primary language(s)
- Framework(s)
- Runtime
- Package manager
- Build system
- Entry points
- Application type
- Database
- Cache
- Queues
- Background workers
- Scheduled jobs
- External APIs
- Authentication system
- Configuration system
- Logging system
- Testing framework
- Deployment platform
- CI/CD
- Docker/container configuration
- Environment variables
- Infrastructure configuration

---

## 2.2 Inspect Important Files

Look for files such as:

- README
- CONTRIBUTING
- package manifests
- dependency files
- lock files
- configuration files
- environment examples
- Dockerfiles
- compose files
- CI workflows
- deployment configuration
- migration files
- schema definitions
- test configuration
- lint configuration
- formatting configuration

Do not assume file names.

Discover them from the repository.

---

# 3. Build an Architecture Map

Before major refactoring, mentally or explicitly map:

```text
User / Client
     ↓
Interface / API
     ↓
Application Logic
     ↓
Domain / Services
     ↓
Data Access
     ↓
Database / External Services
```

Identify where the actual project differs.

Document:

- Major modules
- Responsibilities
- Dependencies
- Data flow
- State flow
- Control flow
- External boundaries
- Persistence boundaries
- Concurrency boundaries

Pay particular attention to:

- Circular dependencies
- Hidden global state
- Shared mutable state
- Tight coupling
- God classes/modules
- God functions
- Duplicate logic
- Cross-layer leakage

---

# 4. Establish a Baseline

Before refactoring, establish the current state.

Record where possible:

### Correctness

- Existing tests
- Known failures
- Known bugs
- Critical workflows

### Performance

- Startup time
- Request latency
- Memory usage
- CPU-heavy operations
- Database-heavy operations

### Quality

- Lint errors
- Type errors
- Static analysis findings
- Complexity hotspots
- Dependency issues

### Reliability

- Crash-prone areas
- Race conditions
- Resource leaks
- Timeout behavior
- Retry behavior
- Failure recovery

Do not optimize based purely on intuition.

Measure when measurement is practical.

---

# 5. Refactoring Priority

Prioritize improvements approximately in this order:

1. Correctness
2. Data integrity
3. Security
4. Reliability
5. Maintainability
6. Testability
7. Observability
8. Performance
9. Developer experience
10. Cosmetic cleanup

Do not sacrifice correctness for elegance.

Do not sacrifice reliability for theoretical performance.

---

# 6. Code Smell Detection

Search systematically for:

## Structural Problems

- God classes
- God functions
- Large modules
- Deep nesting
- Excessive conditionals
- Long parameter lists
- Circular dependencies
- Tight coupling
- Inappropriate inheritance
- Hidden dependencies
- Global mutable state

## Duplication

Look for:

- Repeated logic
- Repeated validation
- Repeated queries
- Repeated error handling
- Repeated configuration logic
- Copy-pasted code

Do not blindly eliminate all duplication.

Some duplication is intentional and can be safer than premature abstraction.

---

# 7. Function and Module Design

Every function should have a clear responsibility.

Prefer:

```text
validate()
load()
transform()
process()
persist()
```

over a single function that performs everything.

Where appropriate:

- Reduce function size
- Reduce nesting
- Reduce parameter count
- Extract coherent responsibilities
- Name operations clearly
- Separate pure logic from side effects

Avoid abstraction for abstraction's sake.

---

# 8. Separation of Concerns

Keep distinct responsibilities separate.

Examples:

```text
UI
Application Logic
Domain Logic
Persistence
Infrastructure
Configuration
Utilities
```

Avoid mixing:

- UI + database operations
- Business rules + HTTP handling
- Configuration + business logic
- Validation + persistence
- Logging + core business logic

The exact architecture should match the project.

Do not impose a framework or architecture merely because it is fashionable.

---

# 9. Dependency Management

Inspect dependencies for:

- Unused packages
- Duplicate packages
- Outdated packages
- Vulnerable packages
- Excessive dependencies
- Unnecessary heavyweight dependencies
- Conflicting versions

Before removing a dependency:

1. Search the repository
2. Check indirect usage
3. Check runtime/import behavior
4. Run tests/build
5. Verify deployment

Never remove dependencies based solely on their apparent lack of direct imports.

---

# 10. Configuration and Environment

Centralize configuration where appropriate.

Separate:

```text
Code
Configuration
Secrets
Environment-specific settings
```

Never hard-code:

- Passwords
- API keys
- Tokens
- Credentials
- Environment-specific paths
- Production URLs
- Machine-specific settings

Validate required configuration at startup when appropriate.

Fail clearly when critical configuration is missing.

---

# 11. Error Handling

Error handling must be intentional.

Avoid:

```text
catch everything
ignore error
return null
continue silently
```

Instead:

- Catch only what can be handled
- Preserve useful error context
- Log appropriately
- Return meaningful errors
- Avoid leaking sensitive information
- Distinguish expected failures from unexpected failures
- Avoid swallowing exceptions

Every recovered error should have a reason.

---

# 12. Logging and Observability

Logs should help answer:

- What happened?
- Where?
- When?
- Why?
- To which operation/request/job?
- What was the impact?

Avoid:

- Excessive logging
- Sensitive data
- Passwords
- Tokens
- Personal data unless required
- Duplicate logs
- Unstructured debugging leftovers

Prefer structured logging when supported by the project.

---

# 13. Database and Persistence

Inspect:

- Connection lifecycle
- Connection pooling
- Transactions
- Query duplication
- N+1 queries
- Missing indexes
- Unsafe queries
- Migration consistency
- Schema assumptions
- Concurrency behavior
- Locking
- Race conditions
- Retry behavior
- Data validation

Never casually modify schemas.

For database changes:

```text
Understand schema
↓
Understand consumers
↓
Plan migration
↓
Implement
↓
Test migration
↓
Test rollback/recovery where applicable
```

---

# 14. Concurrency and Background Work

Pay special attention to:

- Threads
- Processes
- Async operations
- Scheduled tasks
- Background workers
- Queues
- Timers
- Shared resources
- File access
- Database access
- Cache access

Look for:

- Race conditions
- Deadlocks
- Duplicate execution
- Task overlap
- Resource exhaustion
- Improper cancellation
- Unbounded queues
- Zombie processes
- Background work surviving shutdown

Every background task should have:

- Clear ownership
- Clear lifecycle
- Failure handling
- Shutdown behavior
- Resource cleanup

---

# 15. Resource Management

Every acquired resource must have a clear release strategy.

Inspect:

- Database connections
- Files
- Sockets
- HTTP sessions
- Threads
- Processes
- Locks
- Temporary files
- Memory-heavy objects

Prefer lifecycle-safe patterns provided by the language/framework.

---

# 16. API and Interface Stability

Before changing a public interface, identify all consumers.

Check:

- Internal callers
- External clients
- Frontend
- Mobile applications
- Scripts
- Tests
- Integrations
- Documentation

Prefer backward-compatible changes where practical.

If a breaking change is necessary:

1. Document it
2. Update consumers
3. Update tests
4. Update documentation
5. Provide migration guidance

---

# 17. Security Review

During refactoring, actively inspect for:

- Injection vulnerabilities
- Unsafe deserialization
- Authentication weaknesses
- Authorization flaws
- Secret exposure
- Path traversal
- Unsafe file handling
- SSRF
- XSS
- CSRF where relevant
- Insecure defaults
- Excessive permissions
- Sensitive information in logs
- Weak cryptography
- Dependency vulnerabilities

Do not introduce security regressions while improving code quality.

---

# 18. Performance

Performance optimization must be evidence-driven.

First identify:

```text
Actual bottleneck
↓
Root cause
↓
Expected impact
↓
Implementation
↓
Measurement
```

Inspect:

- Algorithmic complexity
- Database queries
- Network calls
- Serialization
- Memory usage
- Repeated computation
- Unnecessary I/O
- Caching opportunities
- Blocking operations
- Startup work

Avoid premature optimization.

Do not make code significantly harder to understand for negligible gains.

---

# 19. Testing Strategy

Tests should protect behavior, not implementation details.

Prioritize:

### Critical workflows

Test:

- Core business logic
- Authentication
- Authorization
- Data integrity
- Important APIs
- Critical user workflows
- Failure paths

### Test types

Use appropriate combinations of:

```text
Unit tests
Integration tests
API tests
Database tests
End-to-end tests
Regression tests
Smoke tests
```

Do not create meaningless tests merely to increase coverage.

---

# 20. Regression Protection

Every important bug discovered during refactoring should result in a regression test when practical.

Pattern:

```text
Bug discovered
↓
Reproduce
↓
Write failing test
↓
Fix
↓
Test passes
↓
Ensure surrounding tests still pass
```

---

# 21. Type Safety and Validation

Where supported:

- Strengthen type definitions
- Remove unsafe casts
- Validate external input
- Validate configuration
- Validate API boundaries
- Validate database assumptions

Do not use type suppression as a substitute for understanding the problem.

---

# 22. Naming

Names should communicate intent.

Prefer:

```text
calculate_total()
validate_submission()
load_user_profile()
```

over:

```text
do_it()
process()
handle()
temp()
data2()
```

Avoid unnecessary abbreviations.

Names should reflect domain meaning.

---

# 23. Comments and Documentation

Comments should explain:

- Why something exists
- Why an unusual approach is necessary
- Important constraints
- Non-obvious business rules
- External limitations

Avoid comments that merely restate code.

Update documentation when behavior changes.

---

# 24. Remove Dead Code

Identify:

- Unused functions
- Unreachable branches
- Deprecated modules
- Old configuration
- Abandoned experiments
- Duplicate implementations
- Temporary debugging code

Before deleting something:

1. Search for references
2. Check dynamic usage
3. Check configuration references
4. Check scripts
5. Check tests
6. Check deployment

Then remove safely.

---

# 25. Simplification

Prefer the simplest design that correctly satisfies requirements.

Simplify:

- Control flow
- APIs
- Configuration
- Dependencies
- Data transformations
- Repeated abstractions
- Unnecessary layers

Do not confuse shorter code with better code.

Clarity is more important than line count.

---

# 26. Architecture Improvement

When recurring problems reveal architectural weaknesses, consider:

- Better module boundaries
- Dependency inversion
- Service extraction
- Domain separation
- Event-driven boundaries
- Queue-based processing
- Better persistence abstraction
- Configuration separation
- Clearer lifecycle management

Architecture changes require stronger validation than local refactoring.

Do not perform large architectural rewrites without evidence.

---

# 27. Refactoring Workflow

Use this workflow for significant changes:

## Phase 1: Discover

- Inspect repository
- Identify architecture
- Identify entry points
- Identify dependencies
- Identify state
- Identify external boundaries
- Identify tests
- Identify known failures

## Phase 2: Diagnose

Create a list:

```text
Critical
High
Medium
Low
```

Classify issues as:

```text
Correctness
Security
Reliability
Maintainability
Performance
Testing
Documentation
Developer Experience
```

## Phase 3: Plan

For each significant issue determine:

```text
Problem
Root Cause
Proposed Change
Affected Components
Risk
Validation Method
Rollback Strategy
```

## Phase 4: Implement

Make small logical changes.

Do not mix unrelated refactoring with feature development unless necessary.

## Phase 5: Validate

After each logical group:

- Run tests
- Run linting
- Run type checking
- Run build
- Run relevant static analysis
- Check logs
- Check important workflows

Use the project's actual tooling.

Never invent commands when the repository already defines them.

## Phase 6: Review

Ask:

- Did behavior remain unchanged?
- Did complexity decrease?
- Did coupling decrease?
- Did reliability improve?
- Did tests improve?
- Did security improve?
- Did performance regress?
- Did documentation become stale?
- Did we introduce unnecessary abstraction?

## Phase 7: Clean Up

Remove:

- Dead code
- Temporary files
- Debug statements
- Unused imports
- Unused dependencies
- Temporary configuration

## Phase 8: Final Verification

Run the broadest practical validation suite.

Then report:

```text
Changes
Tests
Known limitations
Remaining risks
Potential future improvements
```

---

# 28. Change Risk Classification

### Low Risk

- Naming improvements
- Formatting
- Import cleanup
- Local extraction
- Comment improvements

### Medium Risk

- Module restructuring
- Dependency replacement
- Shared utility changes
- Query optimization
- Configuration restructuring

### High Risk

- Database schema changes
- Authentication changes
- Concurrency changes
- Lifecycle changes
- Public API changes
- Major architectural changes
- Deployment changes

High-risk changes require stronger testing and explicit validation.

---

# 29. AI Agent Rules

## NEVER

- Modify code before understanding it
- Assume missing context
- Rewrite the entire project unnecessarily
- Delete code without checking usage
- Replace working architecture merely because another architecture is preferred
- Upgrade dependencies blindly
- Change database schemas casually
- Disable tests to make them pass
- Suppress errors
- Hide warnings
- Remove logging merely because it is inconvenient
- Change behavior under the label of "refactoring"
- Claim something was tested when it was not
- Claim something works without verification

## ALWAYS

- Inspect first
- Explain significant assumptions
- Preserve behavior
- Prefer incremental changes
- Validate changes
- Reuse existing project conventions
- Minimize unnecessary dependencies
- Protect backward compatibility
- Add regression tests for important bugs
- Report uncertainty
- Report unresolved issues honestly

---

# 30. No Blind Rewrite Rule

A rewrite is justified only when there is evidence that incremental refactoring cannot reasonably solve the problem.

Before proposing a rewrite, establish:

1. Current architectural limitations
2. Cost of incremental refactoring
3. Risk of continuing with the current architecture
4. Migration strategy
5. Compatibility strategy
6. Testing strategy
7. Rollback strategy

Prefer migration over replacement when practical.

---

# 31. Definition of Done

A refactoring task is NOT complete merely because the code looks cleaner.

It is complete when:

- [ ] Intended behavior is preserved
- [ ] Root cause has been addressed
- [ ] Tests pass
- [ ] Relevant new tests exist
- [ ] Lint/type checks pass where applicable
- [ ] Build succeeds where applicable
- [ ] No obvious security regression exists
- [ ] No unnecessary dependencies were introduced
- [ ] Dead code was removed where safe
- [ ] Documentation is consistent
- [ ] Error handling is appropriate
- [ ] Resource lifecycle is safe
- [ ] Concurrency behavior is understood
- [ ] Performance was not unintentionally degraded
- [ ] Changes are understandable to another developer
- [ ] Remaining risks are documented

---

# 32. Refactoring Report

After significant refactoring, produce:

```text
## Summary

What changed and why.

## Architecture

What structural improvements were made.

## Correctness

What behavior was preserved or corrected.

## Reliability

What failure modes were addressed.

## Security

What security-related issues were reviewed.

## Performance

What was measured or improved.

## Testing

What tests/checks were executed.

## Remaining Issues

Known limitations or technical debt.

## Recommended Next Steps

Prioritized future improvements.
```

---

# 33. Technical Debt Register

Maintain a lightweight technical debt list.

For each item:

```text
ID:
Area:
Problem:
Impact:
Risk:
Suggested Solution:
Priority:
Status:
```

Prioritize technical debt based on actual impact rather than aesthetics.

---

# 34. Refactoring Quality Score

For significant refactoring, evaluate:

| Area | Question |
|---|---|
| Correctness | Is behavior correct? |
| Architecture | Are responsibilities clearer? |
| Coupling | Are unnecessary dependencies reduced? |
| Cohesion | Do modules have focused responsibilities? |
| Reliability | Are failure modes handled? |
| Security | Are boundaries protected? |
| Performance | Are bottlenecks understood? |
| Testing | Is important behavior protected? |
| Observability | Can failures be diagnosed? |
| Documentation | Can another developer understand it? |
| Maintainability | Is future change easier? |

A refactoring should improve the overall system, not merely one metric.

---

# 35. Golden Rule

Before changing code, understand it.

Before simplifying code, understand why it became complex.

Before deleting code, prove it is unnecessary.

Before optimizing code, measure the bottleneck.

Before changing architecture, understand the system boundaries.

Before changing behavior, obtain explicit authorization.

Before declaring success, validate the result.

The goal is not:

> "Make the code look better."

The goal is:

> "Make the system easier to understand, safer to change, harder to break, and more effective over time."
