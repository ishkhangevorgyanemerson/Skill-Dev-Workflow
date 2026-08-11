# Hardware Question Taxonomy

Use this taxonomy to classify requests before answering.

## A) Conceptual Questions
- Component behavior or selection
- Interface/protocol basics
- System-level constraints and tradeoffs

## B) Setup and Configuration
- Wiring and topology checks
- Instrument/session configuration
- Environment and dependency setup

## C) Troubleshooting and Failure Analysis
- No output/no response
- Intermittent behavior
- Measurement mismatch or drift
- Throughput/performance degradation

## D) Architecture and Decisions
- Build vs buy
- Abstraction boundaries
- Reliability/maintainability tradeoffs

## Routing Rule

- If the request is broad hardware guidance: answer in this skill.
- If the request is deep semiconductor STL code architecture: route to `semiconductor-test-library-assistant`.
- If the request is RF production failure isolation: route to `rf-troubleshooting`.

