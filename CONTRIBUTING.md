Contributing Guidelines – Patient Profile Service

Thank you for contributing! This backend service powers the central patient/member identity layer of our platform. It is designed to be agent-maintainable, schema-driven, and highly interoperable with external systems.

⸻

✅ General Principles
	•	Follow clear and modular patterns
	•	Use docstrings and type hints for every function, class, and Pydantic model
	•	Prioritize declarative and testable code
	•	Structure code for AI agents and human devs to read and extend easily

⸻

🧱 Architecture Notes for Contributors and AI Assistants

1. Pydantic Models
	•	All fields must be explicitly typed
	•	Use nested models where needed (e.g. EmergencyContact)
	•	Attach descriptive docstrings — these are used by AI agents to generate or refactor code

2. Extensions Model
	•	New fields from external systems are not hardcoded
	•	They are defined in YAML files (e.g. hint_fields.yaml) and loaded dynamically into the extensions object
	•	Do not rename or flatten extensions — each vendor (e.g. Hint, Elation) has its own namespace

3. Field Ownership & Trust
	•	Every synced field must include metadata about the source system (e.g. "phone": "hint", "dob": "elation")
	•	Logic that updates fields must respect ownership rules
	•	If a conflicting value is detected, do not overwrite it silently — prefer trust score resolution or human-in-the-loop validation

4. Agent-Aware Coding
	•	Use consistent naming: patient, profile, extensions, source_system
	•	Document assumptions inside comments where logic might seem unclear to a future agent
	•	Avoid inline magic values or logic — use named constants and helper functions

5. Routing and API
	•	Use FastAPI path operation decorators with proper request/response models
	•	Ensure endpoints are self-documenting via docstrings
	•	Avoid untyped dict returns — always use BaseModel

⸻

🚨 What Not to Do
	•	❌ Do not hardcode vendor-specific fields in the patient model
	•	❌ Do not flatten the extensions object
	•	❌ Do not delete or override trust_score without a validated algorithm
	•	❌ Do not remove YAML field support logic from the loader

⸻

✅ Pull Request Checklist
	•	Code uses type hints and Pydantic models
	•	No core schema fields were modified without approval
	•	extensions structure preserved and test-covered
	•	Unit or snapshot tests added for any new logic
	•	Changes described in PR summary with links to issue/task

⸻

Thank you! This system is built for long-term reliability and future AI co-development — your clear, modular contributions make it stronger.