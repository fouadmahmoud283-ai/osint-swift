SWIFT — Full Project Explanation (Developer-Level)
1. What SWIFT actually is (one sentence)
SWIFT is a core-centric AI investigation platform where a central intelligence engine builds and reasons over a knowledge graph, and all modules (Due Diligence, Investigations, Media Analysis, etc.) are just controlled ways of asking that engine questions and generating outputs.
Everything revolves around the Core AI Engine.

2. The mental model (this is key)
Tell your devs this:
“SWIFT is not a set of independent tools.
It is one brain (the Core Engine) with multiple arms (modules).
The brain owns data, logic, memory, and reasoning.
Modules are interfaces and workflows, not intelligence.”
If they get this, they won’t build spaghetti.

3. High-level layers (how the system is divided)
SWIFT has 5 logical layers:
1.	Access & Control Layer (API, auth, cases)
2.	Core AI Engine (the brain)
3.	Modules (use-cases)
4.	Ingestion & Extraction (feeding the brain)
5.	Storage (memory)
Each layer has a single responsibility.

4. Access & Control Layer (how humans enter the system)
Components
•	Web UI (analysts)
•	API Gateway (FastAPI)
•	Auth & Permissions
•	Case Workspace
What this layer does
•	Handles users, sessions, permissions
•	Manages cases (case = investigation container)
•	Never does intelligence work
What it does not do
•	No entity logic
•	No scoring
•	No AI decisions
Relationship
•	Calls Modules
•	Stores metadata in Postgres
•	Never talks directly to Graph DB or Vector DB
Think of this layer as air traffic control, not the plane.

5. Core AI Engine (THE BRAIN)
This is the most important part of SWIFT.
The Core Engine owns:
•	Intelligence
•	Memory
•	Reasoning
•	Consistency
Everything intelligent goes here.

5.1 Orchestrator (the conductor)
Role
•	Controls workflows
•	Decides which engine runs, in what order
•	Handles async vs sync execution
Example
“Run Due Diligence → ingest → extract → resolve entities → score → generate report”
Important
•	Orchestrator never does work itself
•	It routes work

5.2 Entity Resolution Engine
Role
•	Answers: “Are these two things the same real-world entity?”
It does
•	Deduplication
•	Alias merging
•	Confidence scoring
Why it matters
•	Without this, graphs become garbage
•	This is what separates toys from real intel systems
Relationships
•	Reads extracted entities
•	Writes canonical entities to Graph DB
•	Talks to Knowledge Graph Builder

5.3 Knowledge Graph Builder
Role
•	Writes structured truth into the graph
It does
•	Create entities (Person, Org, Location, Event)
•	Create relationships (works_for, linked_to, mentioned_in)
•	Handle temporal edges
Important
•	This is the single writer to the Graph DB
•	No module writes to the graph directly

5.4 Retrieval Layer (RAG but graph-first)
Role
•	Unified access to all memory
It queries
•	Graph DB (relationships, networks)
•	Vector DB (semantic similarity)
•	Object Store (raw evidence)
Why this matters
•	Modules never query databases directly
•	Retrieval abstracts how data is stored

5.5 Scoring & Flag Engine
Role
•	Turns messy intelligence into decisions
It does
•	Risk scores (1–10)
•	Flags (PEP, sanctions, proximity risk)
•	Rule-based + explainable logic
Critical rule
Scores must always be explainable.
This is not a black box model.

5.6 LLM / Model Manager
Role
•	Controls AI models safely
It does
•	Prompt templates
•	Model selection
•	Guardrails
•	No direct database access
Important
•	LLMs never decide truth
•	They summarise, explain, narrate
Truth comes from graph + rules.

5.7 Audit & Evidence Binder
Role
•	Legal defensibility
It does
•	Evidence snapshots
•	Source citations
•	Chain of custody
•	Immutable references
Why
•	If it can’t be audited, it doesn’t exist.

6. Modules (WHAT SWIFT DOES)
Modules are not engines.
They are controlled workflows over the Core Engine.

Example: Automatic Due Diligence (ADD)
ADD does NOT
•	Build graphs
•	Resolve entities
•	Decide scores
ADD DOES
•	Collect subject input
•	Ask the Core Engine questions
•	Assemble outputs into a report

ADD workflow (simple explanation)
1.	User submits subject
2.	ADD generates search plan
3.	Orchestrator triggers ingestion
4.	Extraction produces entities
5.	Entity Resolution cleans identities
6.	Graph Builder stores truth
7.	Scoring Engine assigns risk
8.	LLM narrates findings
9.	Audit Binder locks evidence
10.	Report is generated
ADD is basically:
“A script that asks the brain to think in a specific way.”

Why this design matters
•	You can add new modules without touching the core
•	Every module benefits from existing data
•	Intelligence compounds over time

7. Ingestion & Extraction (feeding the brain)
Ingestion Layer
•	Connectors
•	Scrapers
•	Schedulers
•	Workers
It does
•	Fetch raw data
•	Store it safely
•	Never interprets meaning

Extraction Layer
•	NER
•	Relation extraction
•	Classification
It does
•	Turns text into candidate entities
•	Passes them to Entity Resolution

Key rule
Ingestion and Extraction NEVER decide identity or truth.
They only propose.

8. Storage Layer (memory types)
Each store has one responsibility:
Postgres
•	Users
•	Cases
•	Scores
•	Config
•	Metadata
Graph DB
•	Entities
•	Relationships
•	Networks
Vector DB
•	Semantic similarity
•	Search
•	Recall
Object Store
•	Raw evidence
•	PDFs
•	Media
•	Snapshots

9. How everything talks to everything (important)
Allowed paths
•	UI → API → Module → Core Engine
•	Core Engine → Databases
•	Ingestion → Extraction → Core Engine
Forbidden paths
•	Modules → Databases 
•	UI → Graph DB 
•	LLM → Truth decisions 
This prevents chaos.

10. How you should explain roles to devs
Core Engine Dev
“You are building intelligence primitives.
You never care about UI or reports.”
Module Dev
“You are designing investigative workflows, not AI logic.”
API Dev
“You manage access, safety, and structure — not intelligence.”

11. One sentence summary to end with (use this)
“SWIFT is a graph-first intelligence platform where the Core Engine owns truth and reasoning, modules define investigative workflows, and everything is explainable, auditable, and extensible.”


