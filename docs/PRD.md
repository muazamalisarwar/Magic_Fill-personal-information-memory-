# Product Requirements Document (PRD)

# Personal Information Memory & Intelligent Form Completion (Magic Fill)

**An Intelligent Autofill and Reusable Profile Memory Ecosystem with Semantic Field Understanding and Contextual Experience Relevance**

---

## 1. Document Information

| Attribute | Details |
| :--- | :--- |
| **Project Title** | Personal Information Memory & Intelligent Form Completion (**Magic Fill**) |
| **Document Type** | Product Requirements Document (PRD) |
| **Document Version** | 1.0.0 |
| **Document Status** | Approved Baseline for Development Phase 1 |
| **Academic Context** | University Final Year Project (FYP) / Capstone Software Engineering Project |
| **Repository Path** | `muazamalisarwar/Magic_Fill-personal-information-memory-` |
| **Target Platforms** | Web Application, REST API Backend, Chromium Browser Extension |
| **Date of Baseline** | September 2026 |

---

## 2. Team Members & Responsibilities

The project is developed by a four-member engineering team with clear separation of concerns across backend, database, vector/semantic memory, and frontend/form interaction.

| Team Member | Core Domain | Major Components & Assigned Responsibilities | Current Progress Status |
| :--- | :--- | :--- | :--- |
| **Muazam Ali** | **FastAPI & Backend Architecture** | • FastAPI application lifecycle and middleware configuration<br>• RESTful API endpoint design and routing (`/api/users`, `/api/users/{id}/personal-info`, `/api/users/{id}/experiences`, `/api/experiences/{id}`)<br>• Pydantic v2 request/response schemas with strict validation<br>• Centralized and sanitized error handling (custom `AppException` & HTTP status codes)<br>• Service layer decoupling business logic from API routers<br>• Database session dependency injection (`get_db`)<br>• Automated API documentation (Swagger UI `/docs`, ReDoc `/redoc`)<br>• Comprehensive automated unit & integration testing suite with Pytest<br>• Extensible integration architecture prepared for AI/Vector layer integration | **Implemented & Verified**<br>*(15/15 Pytest tests passing, 100% operational)* |
| **Adeel** | **Database & Data Layer** | • Relational database architecture (PostgreSQL primary, SQLite local fallback)<br>• Relational entity design: `users`, `personal_info`, `experiences`<br>• Entity relationship design: `User 1:1 PersonalInfo`, `User 1:N Experiences`<br>• Foreign key constraints, cascading deletion (`CASCADE`), and index optimization<br>• Data consistency, constraints, and timestamping (`created_at`, `updated_at`)<br>• Integration with SQLAlchemy 2.0 ORM engine<br>• Supporting future semantic/vector memory data synchronization<br>• Migration strategy (Alembic) and database integrity testing | **Initial Relational Models Implemented**;<br>*Production migrations & connection pooling Planned* |
| **Qasim** | **Vector Database & Semantic Memory** | • Vector database selection, setup, and configuration (FAISS / pgvector / Chroma)<br>• Embedding model selection and pipeline (Sentence Transformers, e.g., `all-MiniLM-L6-v2`)<br>• Vector representation of personal information attributes and work experiences<br>• Semantic field mapping engine (matching arbitrary external form field labels to stored profile keys)<br>• Contextual experience relevance ranking algorithm (scoring experiences against job descriptions)<br>• Vector similarity search and top-$K$ candidate retrieval<br>• Preparing vector-memory service interfaces for FastAPI backend consumption<br>• Precision and recall testing of semantic retrieval | **Planned**<br>*(No vector code exists in repository yet; decoupled interface ready)* |
| **Hussnain** | **Frontend & Form Interaction** | • User web dashboard for viewing and editing personal profile information<br>• Experience management interface (adding, updating, and categorizing multiple roles)<br>• Chromium browser extension (Manifest V3) for automated form interaction<br>• Web form field detection and DOM parsing engine<br>• Visual floating UI / modal for displaying AI-matched suggestions<br>• Visual confidence scoring indicators (High, Medium, Low)<br>• Interactive human-in-the-loop confirmation (Accept, Reject, Edit inline)<br>• Automated form input population (autofill execution)<br>• Frontend-to-backend REST API integration | **Planned**<br>*(No frontend or browser extension code in repository yet)* |

---

## 3. Executive Summary

Digital applications across employment portals (LinkedIn, Indeed, Workday), university admission platforms, visa applications, scholarship submissions, and government portals require users to repeatedly input the same biographical, contact, academic, and professional information. 

Current browser autofill solutions (e.g., standard browser auto-complete) rely on rudimentary syntactic attribute matching (such as `name="first_name"` or `id="email"`). When an external web form uses non-standard, arbitrary, or dynamically generated identifiers (e.g., `Applicant Legal Name`, `Nominee Full Name`, `txt_q7_fname`, or `field_89234`), conventional autofill tools fail entirely. Furthermore, when completing applications that require professional experience, conventional tools cannot evaluate the **context** of the job description to select and recommend the user's most relevant experiences from their career history.

**Magic Fill (Personal Information Memory & Intelligent Form Completion)** solves this problem by creating an intelligent personal memory system that:
1. Stores structured personal, academic, and multi-experience records in a relational database.
2. Converts profile fields and experiences into vector embeddings stored in a vector database.
3. Performs **semantic field mapping** to recognize the underlying meaning of external form fields regardless of their HTML naming conventions.
4. Performs **contextual experience relevance ranking** to recommend the user's most fitting experiences for specific application contexts.
5. Keeps the **user strictly in control** via a non-intrusive confirmation interface that displays confidence levels and allows manual correction before any data is filled.

---

## 4. Problem Statement

### 4.1 Form Fatigue and Redundancy
Candidates applying for academic programs or employment opportunities spend hundreds of hours manually transcribing the same personal, educational, and professional data into diverse online forms.

### 4.2 Syntactic Brittle-Matching Failure
Standard browser autocomplete mechanisms depend strictly on HTML standard attributes:
- An input tag with `name="email"` is easily identified.
- An input tag with `name="applicant_primary_electronic_mail"` or an unlabelled `input` surrounded by custom `<div>` text is missed.
- The same underlying semantic datum (Full Name) is represented in diverse ways across websites:
  - `Full Name`
  - `Applicant Name`
  - `Candidate Name`
  - `Name of Applicant`
  - `Legal Name`
  - `Nominee Name`

A purely syntactic parser cannot resolve these synonyms.

### 4.3 The Multi-Experience Context Dilemma
Users accumulate multiple diverse experiences over time (e.g., *Software Development Intern*, *AI/ML Research Assistant*, *CMS Developer*, *Teaching Assistant*). When applying for a specialized position (such as a Computer Vision Engineer), submitting all experiences or random experiences degrades application quality. The user needs an intelligent agent that reads the job context, identifies which stored experiences demonstrate required skills, and recommends them with ranked relevance for user confirmation.

---

## 5. Proposed Solution

Magic Fill decouples storage into a **dual-database paradigm**:
1. **Relational Layer:** Guarantees atomicity, consistency, and exact retrieval for canonical profile data and user credentials.
2. **Semantic / Vector Layer:** Enables fuzzy, meaning-based matching between external form fields and internal user profile attributes, as well as contextual similarity scoring between job postings and past experiences.

```text
External Web Form (DOM)                Personal Memory System
┌────────────────────────┐             ┌───────────────────────────────────┐
│ Label: "Candidate Name"│ ──Semantic──│ Canonical: "full_name"            │
│ Value: [             ] │  Matching   │ Stored Value: "Muazam Ali"        │
└────────────────────────┘             └───────────────────────────────────┘
```

The system never operates as an opaque "black-box" auto-submitter. It functions as an **intelligent pair-assistant**, presenting suggestions with confidence metrics and awaiting human confirmation before populating fields.

---

## 6. Product Vision

To become the universal, privacy-centric personal memory layer for the web, eliminating repetitive data entry while ensuring candidates present their most relevant qualifications to every opportunity with complete personal oversight.

---

## 7. Goals & Objectives

### 7.1 Quantitative Goals
- **Field Matching Accuracy:** Achieve $> 90\%$ semantic accuracy in mapping external form labels to canonical profile attributes across standard job portals.
- **Latency:** API response times for semantic field matching $< 250\text{ ms}$; standard relational CRUD operations $< 50\text{ ms}$.
- **Form Completion Efficiency:** Reduce manual form completion time by at least $70\%$ for multi-section job applications.
- **Reliability:** Maintain zero data loss and $> 99.5\%$ backend availability.

### 7.2 Qualitative Goals
- Intuitive, frictionless browser extension interface requiring minimal clicks.
- Transparent confidence display to prevent user anxiety regarding inaccurate data entry.
- Clean, modular codebase suitable for university capstone evaluation and future open-source/commercial deployment.

---

## 8. Target Users

1. **Job Applicants & Students:** Recent graduates and university students applying to dozens of internships and junior roles with varying application requirements.
2. **Freelancers & Contractors:** Professionals regularly submitting proposals, onboarding forms, and profile registrations across diverse platforms.
3. **University Applicants:** Students submitting identical academic transcripts and biographic records to multiple university and scholarship portals.

---

## 9. Scope

### In-Scope
- FastAPI REST backend providing structured CRUD operations for user profiles and multi-role work experiences.
- Relational database schema with 1:1 and 1:N constraints (PostgreSQL production, SQLite testing/local fallback).
- Pydantic validation for all incoming and outgoing data payloads.
- Vector database interface and embedding model pipeline for semantic field matching and experience ranking.
- Chromium browser extension (Manifest V3) for DOM field detection, suggestion display, and autofill execution.
- Web dashboard for profile and experience management.
- Human-in-the-loop review and confirmation workflow.

### Out-of-Scope (Future / Excluded)
- Automated CAPTCHA, reCAPTCHA, or Cloudflare challenge bypassing.
- Payment gateway autofill (credit card numbers, CVVs, banking credentials).
- Fully autonomous submission (clicking "Submit Application" without human confirmation).
- Native mobile application (iOS/Android) autofill.

---

## 10. Product Features

### 10.1 Personal Information Memory (Canonical Profile)
Stores a single canonical personal, academic, and contact profile per user:
- **Biographical:** Full name, father's name, date of birth, national ID / CNIC.
- **Contact:** Phone number, email address, physical street address, city, postal code, country.
- **Academic:** University name, degree program, department/faculty, current semester/standing, registration/roll number.

### 10.2 Experience Memory (Multi-Role Portfolio)
Stores multiple independent employment, internship, and project experiences for each user:
- Organization / Company name.
- Job title / Role.
- Start date and End date (with explicit `null` support indicating currently active / ongoing roles).
- Detailed description of responsibilities and achievements.
- Acquired skills and technologies.

### 10.3 Semantic Field Mapping
Resolves semantic equivalence between external form field descriptors and internal profile fields:
- Encodes external field labels, placeholders, and aria-labels into vector space.
- Calculates cosine similarity against embedded canonical attribute vectors.
- Maps fields above a defined similarity threshold (e.g., $\ge 0.75$) automatically; flags intermediate scores for confirmation.

### 10.4 Contextual Experience Relevance
Evaluates the text of a target job description or form context against the user's stored experiences:
- Converts the job description requirements into an embedding vector.
- Ranks stored experiences based on semantic similarity.
- Recommends the top-$K$ most relevant experiences for the application rather than flooding the form with unrelated past positions.

### 10.5 Confidence Engine & User Confirmation
Every automated match produces a confidence score:
- **High Confidence ($\ge 85\%$):** Field is highlighted in green with suggested value ready for one-click confirmation.
- **Medium Confidence ($60\% - 84\%$):** Field is highlighted in amber; the system displays alternative interpretations for user selection.
- **Low Confidence ($< 60\%$):** Field is left blank; user is prompted to map manually if desired.
- **User Confirmation Guarantee:** Autofill values are never written to the DOM without explicit user approval.

### 10.6 Memory Updates & Conflict Resolution
When a user manually modifies an autofilled field (e.g., changes phone number or enters a new graduation year), the system identifies the delta and prompts:
1. **Update Existing:** Overwrite the stored canonical value with the newly entered value.
2. **Keep Existing:** Keep the stored value and discard the delta for future forms.
3. **Save Alternative:** Store as a secondary contact/address alternative.

### 10.7 Frontend & Form System
- **Web Dashboard:** Clean web interface for creating user accounts, reviewing stored biographical details, and adding/editing past work experiences.
- **Extension Overlay:** Non-disruptive iframe/shadow-DOM overlay that detects form inputs, displays match cards, and triggers filling actions.

### 10.8 FastAPI Backend
- Modular, decoupled architecture separating Routers, Schemas, Services, and Database Models.
- Automatic Swagger (`/docs`) and ReDoc (`/redoc`) API documentation.
- Standardized API response and error envelopes.

### 10.9 Relational Database
- PostgreSQL relational engine with ACID compliance and referential integrity.
- Zero-configuration SQLite fallback for offline development and local automated tests.

### 10.10 Vector Database
- Dedicated embedding store (FAISS / pgvector / Chroma) storing float32 vector representations of text attributes for sub-second nearest-neighbor retrieval.

---

## 11. System Architecture

### 11.1 Conceptual Architecture

```text
                                  USER
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            FRONTEND DASHBOARD            WEB FORM / EXTENSION
             (Hussnain - UI)               (Hussnain - Forms)
                    │                               │
                    └───────────────┬───────────────┘
                                    │ HTTP / REST
                                    ▼
                             FASTAPI BACKEND
                          (Muazam Ali - Backend)
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          RELATIONAL DATABASE               VECTOR DATABASE
         (Adeel - Data Layer)            (Qasim - Semantic DB)
         ┌───────────────────┐           ┌───────────────────┐
         │ PostgreSQL/SQLite │           │  FAISS / pgvector │
         │   users           │           │ Field Embeddings  │
         │   personal_info   │           │ Exp Embeddings    │
         │   experiences     │           │ Context Index     │
         └───────────────────┘           └───────────────────┘
                    │                               │
                    │   ┌───────────────────────┐   │
                    └──>│  AI / MATCHING LAYER  │<──┘
                        │ (Semantic Field Map & │
                        │ Experience Relevance) │
                        └───────────┬───────────┘
                                    │
                                    ▼
                         CONFIDENCE ENGINE &
                          USER CONFIRMATION
                                    │
                                    ▼
                          FORM AUTOFILL COMPLETE
```

### 11.2 Concrete Technical Architecture (Current Repository Baseline)

The current repository represents the core foundational layer of this architecture:

```text
HTTP Client (Browser / Postman / Tests)
               │
               ▼
      [FastAPI Application] (backend/app/main.py)
         ├── CORS Middleware
         ├── Global Sanitized Exception Handlers (AppException, 422, 500)
         └── OpenAPI / Swagger Documentation
               │
               ▼
      [API Router Layer] (backend/app/routers/)
         ├── users.py           (/api/users)
         ├── personal_info.py   (/api/users/{id}/personal-info)
         └── experiences.py     (/api/users/{id}/experiences, /api/experiences/{id})
               │
               ▼
      [Pydantic Validation] (backend/app/schemas/)
         ├── UserCreate, UserResponse
         ├── PersonalInfoCreate, PersonalInfoUpdate, PersonalInfoResponse
         └── ExperienceCreate, ExperienceUpdate, ExperienceResponse (Cross-field Date Validator)
               │
               ▼
      [Business Service Layer] (backend/app/services/)
         ├── user_service.py
         ├── personal_info_service.py (Enforces 1:1, Handles Partial Updates)
         └── experience_service.py (Chronological Ordering, Date Range Checking)
               │
               ▼
      [SQLAlchemy 2.0 ORM & Database] (backend/app/database/)
         ├── models.py (User, PersonalInfo, Experience with FK Cascades)
         └── database.py (SessionLocal, get_db Dependency)
               │
               ▼
      [Relational Storage Engine]
         ├── PostgreSQL (Production via psycopg2-binary)
         └── SQLite (Local development & in-memory automated test suite)
```

---

## 12. End-to-End Workflow

```text
[Step 1] User stores Personal Info & Experiences in Dashboard/Backend.
   │
[Step 2] User navigates to external form (e.g. Job Portal) with Browser Extension active.
   │
[Step 3] Extension scans DOM inputs, extracting labels, placeholders, and aria tags.
   │
[Step 4] Extension transmits field metadata to FastAPI Backend: POST /api/matching/fields.
   │
[Step 5] Backend queries Vector Database for nearest-neighbor semantic matches.
   │
[Step 6] If the form requires work experience, Backend receives Job Description, 
         computes relevance score against stored experiences, and returns ranked list.
   │
[Step 7] Backend returns mapped suggestions with Confidence Scores (0 - 100%).
   │
[Step 8] Extension renders non-intrusive Suggestion Overlay in browser.
   │
[Step 9] User reviews suggestions:
         ├── Accepts all (High Confidence)
         ├── Adjusts / rejects uncertain fields
         └── Selects which of the ranked experiences to populate
   │
[Step 10] Extension populates the confirmed fields in the target web form DOM.
```

---

## 13. Functional Requirements

### 13.1 User & Identity Management
- **FR-01:** The system shall allow creation of new user identity records via `POST /api/users`.
- **FR-02:** The system shall retrieve an existing user's record and metadata via `GET /api/users/{user_id}`.
- **FR-03:** The system shall return HTTP 404 with a structured error response if a requested user does not exist.

### 13.2 Personal Information Management
- **FR-04:** The system shall allow a user to create a personal information record containing biographical, contact, and academic details via `POST /api/users/{user_id}/personal-info`.
- **FR-05:** The system shall strictly enforce a 1-to-1 relationship between User and Personal Information, rejecting duplicate creation attempts with HTTP 400.
- **FR-06:** The system shall retrieve a user's personal information profile via `GET /api/users/{user_id}/personal-info`.
- **FR-07:** The system shall support partial updates to personal information via `PUT /api/users/{user_id}/personal-info`, preserving existing fields not present in the update payload.
- **FR-08:** The system shall validate email address syntax using `EmailStr`.
- **FR-09:** The system shall validate national identity numbers (CNIC), phone numbers, and string lengths against schema constraints.

### 13.3 Experience Management
- **FR-10:** The system shall allow a user to add multiple independent experience entries via `POST /api/users/{user_id}/experiences`.
- **FR-11:** The system shall retrieve all experiences for a user via `GET /api/users/{user_id}/experiences`, returned in reverse chronological order (newest `start_date` first).
- **FR-12:** The system shall retrieve a specific experience entry by its ID via `GET /api/experiences/{experience_id}`.
- **FR-13:** The system shall support partial updates to an experience entry via `PUT /api/experiences/{experience_id}`.
- **FR-14:** The system shall enforce date consistency on experiences, verifying that `end_date >= start_date` when `end_date` is provided.
- **FR-15:** The system shall permit `end_date` to be `null` to represent currently ongoing or active roles.

### 13.4 Semantic Field Mapping (Planned)
- **FR-16:** The system shall convert stored profile attribute names and descriptions into semantic vector embeddings.
- **FR-17:** The system shall receive arbitrary field labels from external forms, generate embeddings, and compute cosine similarity against stored attribute embeddings.
- **FR-18:** The system shall map external field labels to the most semantically similar profile attribute if the similarity exceeds a configurable threshold.

### 13.5 Experience Relevance Ranking (Planned)
- **FR-19:** The system shall accept a target job description or application context as input.
- **FR-20:** The system shall compute contextual semantic relevance scores between the job description and each stored experience.
- **FR-21:** The system shall return a ranked list of recommended experiences for the user to select from.

### 13.6 User Confirmation & Autofill (Planned)
- **FR-22:** The system shall display AI-generated suggestions with visual confidence ratings prior to form insertion.
- **FR-23:** The system shall require user confirmation before populating values into target form fields.
- **FR-24:** The system shall allow users to override or reject any suggested value inline.
- **FR-25:** The system shall detect when a user enters updated information that differs from stored memory and prompt the user to update the database.

---

## 14. Non-Functional Requirements

### 14.1 Security
- **NFR-01:** Database connection credentials, secret keys, and passwords must never be committed to source control or exposed in API error traces.
- **NFR-02:** All API input payloads must be strictly validated and sanitized through Pydantic schemas with extra fields forbidden (`extra="forbid"`).
- **NFR-03:** Foreign key constraints with cascading deletes must prevent orphaned records in relational tables.
- **NFR-04:** Global exception handlers must sanitize raw database errors, returning standardized error messages without leaking database schema internals.

### 14.2 Privacy
- **NFR-05:** User personal data must remain private and accessible only to the authenticated owner.
- **NFR-06:** No personal profile data or form entries shall be logged in plain text within server application logs.

### 14.3 Performance & Scalability
- **NFR-07:** Standard relational CRUD API endpoints must achieve response latency $< 50\text{ ms}$ under normal loads.
- **NFR-08:** The database engine must support connection pooling and pre-ping checks (`pool_pre_ping=True`) to maintain connection health.
- **NFR-09:** Semantic field retrieval should complete in $< 250\text{ ms}$ for forms containing up to 30 fields.

### 14.4 Maintainability & Modularity
- **NFR-10:** Codebase must adhere to a strict layered design: `Routers -> Schemas -> Services -> Models -> Database`.
- **NFR-11:** Database models must remain decoupled from vector storage logic so that vector technology (FAISS, pgvector, Chroma) can be swapped without altering relational contracts.

### 14.5 Reliability & Fault Tolerance
- **NFR-12:** If the vector database or semantic matching service is unavailable, the relational backend must continue operating normally for standard profile management.
- **NFR-13:** A failure in the browser extension must not break or disable the target web form's native functionality.

---

## 15. User Stories

### US-01: Personal Information Storage & Retrieval
- **As a** student or job applicant,
- **I want to** store my biographical, contact, and academic details once in a centralized memory,
- **So that** I do not have to repeatedly type these details across dozens of application portals.
- **Acceptance Criteria:**
  - Can create personal profile via API with full name, CNIC, email, phone, and university details.
  - Can retrieve the stored profile accurately.
  - Cannot create more than one personal profile per user ID.
  - Can perform partial updates to update address or semester standing.

### US-02: Multi-Role Experience Portfolio
- **As a** job applicant with varied internship and project experience,
- **I want to** store multiple work experiences independently with start/end dates and skill tags,
- **So that** my entire career history is available for automated matching.
- **Acceptance Criteria:**
  - Can register multiple experiences for a single user ID.
  - Retrieving user experiences returns a chronological list with newest roles first.
  - Active roles with `end_date = null` are fully supported.
  - Setting `end_date` earlier than `start_date` is rejected with HTTP 422.

### US-03: Semantic Form Field Understanding
- **As a** user filling an external job application,
- **I want** the system to understand that *"Applicant Full Name"* or *"Candidate Legal Name"* means `full_name`,
- **So that** non-standard field names are automatically identified without manual intervention.
- **Acceptance Criteria:**
  - External labels with synonymous terminology are matched to stored canonical fields.
  - Matches are returned with associated confidence scores.

### US-04: Contextual Experience Relevance
- **As a** candidate applying for a machine learning position,
- **I want** the system to recommend my AI/ML internships over unrelated roles,
- **So that** my application is tailored to the job requirements.
- **Acceptance Criteria:**
  - System accepts job description text and computes relevance scores for all stored experiences.
  - Top relevant experiences are prioritized in the recommendation interface.
  - User can selectively choose which recommended experiences to insert.

### US-05: Human-in-the-Loop Confirmation
- **As a** user who values data accuracy,
- **I want** to preview and confirm all suggested values before they are filled into the form,
- **So that** incorrect or hallucinated information is never submitted to an employer.
- **Acceptance Criteria:**
  - Extension displays a confirmation card showing proposed field mappings.
  - User can accept, reject, or edit any value before insertion.
  - Form fields are populated only after explicit user confirmation.

### US-06: Memory Delta Conflict Resolution
- **As a** user who moved to a new address,
- **I want** the system to ask if I wish to update my permanent profile when I enter a new address on a form,
- **So that** my personal memory stays updated over time.
- **Acceptance Criteria:**
  - System detects discrepancy between form value and stored memory.
  - Presents user with options: "Update Existing", "Keep Existing", or "Save Alternative".

---

## 16. API Requirements (FastAPI Backend)

All endpoints return a standardized response envelope. Implemented endpoints have been verified against the running server and automated test suite.

### 16.1 Standard Response Envelopes

#### Success Envelope (`200 OK` / `201 Created`):
```json
{
  "success": true,
  "message": "Human-readable confirmation message",
  "data": { ... }
}
```

#### Error Envelope (`400`, `404`, `422`, `500`):
```json
{
  "success": false,
  "message": "Human-readable error description",
  "error_code": "MACHINE_READABLE_CODE",
  "details": [ ... ]
}
```

### 16.2 Endpoints Specification Table

| Method | Endpoint URL | Purpose | Request Body | Response Model | Validation Rules | Error Codes | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | System health check and status | None | `HealthResponse` | None | None | **Implemented** |
| `POST` | `/api/users` | Register a new user identity | `UserCreate` (optional `{}`) | `APIResponse[UserResponse]` | Extra fields forbidden | `500` | **Implemented** |
| `GET` | `/api/users/{user_id}` | Retrieve user record by ID | None | `APIResponse[UserResponse]` | `user_id > 0` | `USER_NOT_FOUND` (404) | **Implemented** |
| `POST` | `/api/users/{user_id}/personal-info` | Create 1:1 personal profile | `PersonalInfoCreate` | `APIResponse[PersonalInfoResponse]` | `full_name` min 2 chars; valid `email`; `user_id > 0` | `USER_NOT_FOUND` (404), `PERSONAL_INFO_ALREADY_EXISTS` (400), `VALIDATION_ERROR` (422) | **Implemented** |
| `GET` | `/api/users/{user_id}/personal-info` | Retrieve personal profile | None | `APIResponse[PersonalInfoResponse]` | `user_id > 0` | `USER_NOT_FOUND` (404), `PERSONAL_INFO_NOT_FOUND` (404) | **Implemented** |
| `PUT` | `/api/users/{user_id}/personal-info` | Partial update personal profile | `PersonalInfoUpdate` | `APIResponse[PersonalInfoResponse]` | Optional fields; validates non-null items | `USER_NOT_FOUND` (404), `PERSONAL_INFO_NOT_FOUND` (404), `VALIDATION_ERROR` (422) | **Implemented** |
| `POST` | `/api/users/{user_id}/experiences` | Create new work experience | `ExperienceCreate` | `APIResponse[ExperienceResponse]` | `company`, `job_title`, `start_date` required; `end_date >= start_date` | `USER_NOT_FOUND` (404), `VALIDATION_ERROR` (422) | **Implemented** |
| `GET` | `/api/users/{user_id}/experiences` | List all experiences for user | None | `APIResponse[List[ExperienceResponse]]` | `user_id > 0` | `USER_NOT_FOUND` (404) | **Implemented** |
| `GET` | `/api/experiences/{experience_id}` | Retrieve single experience | None | `APIResponse[ExperienceResponse]` | `experience_id > 0` | `EXPERIENCE_NOT_FOUND` (404) | **Implemented** |
| `PUT` | `/api/experiences/{experience_id}` | Update experience by ID | `ExperienceUpdate` | `APIResponse[ExperienceResponse]` | Cross-field date check if dates changed | `EXPERIENCE_NOT_FOUND` (404), `INVALID_DATE_RANGE` (400), `VALIDATION_ERROR` (422) | **Implemented** |
| `POST` | `/api/matching/fields` | Match external form fields to profile | `FieldMatchRequest` | `APIResponse[FieldMatchResponse]` | List of label strings | `VECTOR_DB_UNAVAILABLE` (503) | **Planned** |
| `POST` | `/api/matching/experiences` | Rank experiences by job context | `ExperienceRankRequest` | `APIResponse[List[RankedExperience]]` | Job description text | `VECTOR_DB_UNAVAILABLE` (503) | **Planned** |

---

## 17. Database Requirements

The data tier is conceptually split into a **Relational Store** (managed by Adeel) and a **Vector Store** (managed by Qasim).

```text
                                  DATABASE LAYER
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       RELATIONAL DATABASE (Adeel)              VECTOR DATABASE (Qasim)
  ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
  │ Engine: PostgreSQL (SQLite local) │   │ Engine: FAISS / pgvector / Chroma │
  │ Paradigm: ACID, Normalized, Rel.  │   │ Paradigm: High-dimensional Vector │
  ├───────────────────────────────────┤   ├───────────────────────────────────┤
  │ Tables:                           │   │ Indices:                          │
  │ • users (id, created_at, ...)     │   │ • Field embeddings (384-d / 768-d)│
  │ • personal_info (1:1 with users)  │   │ • Experience semantic embeddings  │
  │ • experiences (1:N with users)    │   │ • Metric: Cosine Similarity       │
  └───────────────────────────────────┘   └───────────────────────────────────┘
```

### 17.1 Relational Database Specification (Implemented)

#### Table: `users`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Autoincrement, Index | Unique internal user identifier |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()`, Not Null | User registration timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()`, On Update `now()`, Not Null | Record update timestamp |

#### Table: `personal_info`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Autoincrement, Index | Unique record ID |
| `user_id` | `INTEGER` | Foreign Key (`users.id`, `ON DELETE CASCADE`), Unique, Not Null, Index | Enforces 1-to-1 relationship with User |
| `full_name` | `VARCHAR(150)` | Not Null | User's full legal name |
| `father_name` | `VARCHAR(150)` | Nullable | Father's name |
| `date_of_birth` | `DATE` | Nullable | Date of birth (YYYY-MM-DD) |
| `cnic` | `VARCHAR(20)` | Nullable, Index | National ID card number |
| `phone` | `VARCHAR(30)` | Nullable | Primary contact phone number |
| `email` | `VARCHAR(255)` | Nullable | Primary email address |
| `address` | `TEXT` | Nullable | Street / residential address |
| `city` | `VARCHAR(100)` | Nullable | City of residence |
| `postal_code` | `VARCHAR(20)` | Nullable | Postal / ZIP code |
| `country` | `VARCHAR(100)` | Nullable | Country of residence |
| `university` | `VARCHAR(200)` | Nullable | University / college name |
| `degree` | `VARCHAR(150)` | Nullable | Degree program name |
| `department` | `VARCHAR(150)` | Nullable | Academic department |
| `semester` | `VARCHAR(50)` | Nullable | Current semester / standing |
| `registration_number` | `VARCHAR(100)` | Nullable | Student registration / roll number |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()`, Not Null | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()`, On Update `now()`, Not Null | Last update timestamp |

#### Table: `experiences`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Autoincrement, Index | Unique experience record ID |
| `user_id` | `INTEGER` | Foreign Key (`users.id`, `ON DELETE CASCADE`), Not Null, Index | Enforces 1-to-N relationship with User |
| `company` | `VARCHAR(200)` | Not Null | Employer / organization name |
| `job_title` | `VARCHAR(150)` | Not Null | Job title / position held |
| `start_date` | `DATE` | Not Null | Employment start date |
| `end_date` | `DATE` | Nullable | End date; `null` signifies active position |
| `description` | `TEXT` | Nullable | Roles, duties, accomplishments |
| `skills` | `TEXT` | Nullable | Comma-separated or listed skills |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()`, Not Null | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()`, On Update `now()`, Not Null | Last update timestamp |

### 17.2 Vector Database Specification (Planned)

- **Vector Engine Candidate:** FAISS (in-memory / file index for fast local retrieval) or `pgvector` (PostgreSQL extension enabling unified relational and vector storage).
- **Embedding Dimensions:** 384 dimensions (using `sentence-transformers/all-MiniLM-L6-v2`) or 768 dimensions (using `all-mpnet-base-v2`).
- **Distance Metric:** Cosine Similarity / Inner Product normalized.
- **Indexed Entities:**
  1. Profile Attribute Labels & Descriptions (e.g., `"full_name"`, `"cnic"`, `"university"`, `"degree"`).
  2. Experience Text Blocks (concatenation of `job_title + company + description + skills`).
  3. Form Field Contextual Embeddings (form field label, placeholder, surrounding HTML text).

---

## 18. AI & Semantic Requirements

### 18.1 Semantic Field Mapping Pipeline
1. **Extraction:** Browser extension extracts `<label>`, `placeholder`, `aria-label`, and `name` attributes from an external form field.
2. **Preprocessing:** Strip special characters, lower-case, and format label strings (e.g., `"applicant_first_name_txt"` $\rightarrow$ `"applicant first name"`).
3. **Embedding:** Pass text through embedding model to generate a 384-dimensional dense vector.
4. **Nearest Neighbor Search:** Query the vector index against all stored canonical profile attributes.
5. **Threshold Evaluation:**
   - Score $\ge 0.85$: High confidence match.
   - Score $0.65 - 0.84$: Medium confidence match (requires user selection).
   - Score $< 0.65$: Unmapped (no autofill suggestion).

### 18.2 Contextual Experience Relevance Algorithm
1. **Context Ingestion:** Extract job posting title, description, and required qualifications from the application page.
2. **Context Vectorization:** Embed the job description context into the shared vector space.
3. **Relevance Computation:** For each stored experience $E_i$ of the user, compute cosine similarity:
   $$\text{Relevance}(E_i, \text{Job}) = \frac{\mathbf{v}_{\text{job}} \cdot \mathbf{v}_{E_i}}{\|\mathbf{v}_{\text{job}}\| \|\mathbf{v}_{E_i}\|}$$
4. **Ranking:** Sort experiences in descending order of relevance score.
5. **Payload Generation:** Return experiences ranked by score, allowing the user to select the top 1, 2, or 3 roles to fill into multi-experience form fields.

---

## 19. Frontend & Form Requirements (Planned)

### 19.1 Web Dashboard (Hussnain)
- Responsive, clean interface for user profile management.
- Tab 1: **Personal Details** (Form for editing biographical, contact, and academic fields).
- Tab 2: **Experiences Portfolio** (Cards for adding, editing, and deleting past internships and jobs).
- Tab 3: **Form History & Settings** (Logs of past forms filled and confidence sensitivity settings).

### 19.2 Chromium Browser Extension (Hussnain)
- **Manifest V3 Architecture:**
  - `manifest.json`: Configuration, permissions (`activeTab`, `storage`, `scripting`).
  - `background.js`: Service worker managing communication between content scripts and FastAPI backend.
  - `content.js`: Injected into external web pages to inspect DOM, identify `<input>`, `<select>`, `<textarea>` elements, and extract labels.
  - `popup.html / popup.js`: Extension toolbar popup showing quick user status and on/off autofill toggle.
- **In-Page Floating UI / Overlay:**
  - Rendered via a Shadow DOM to avoid CSS collisions with the host page.
  - Displays match status: *"Magic Fill identified 8 fields. Click to review and confirm."*
  - Shows confidence badges (Green, Yellow) next to detected fields.
  - One-click confirmation button to populate fields.

---

## 20. Acceptance Criteria

| ID | Acceptance Criteria | Target Component | Status |
| :--- | :--- | :--- | :--- |
| **AC-01** | Backend starts successfully via Uvicorn and responds to `GET /health` with `status: "healthy"`. | FastAPI Backend | **Verified & Passing** |
| **AC-02** | User identity can be created via `POST /api/users` returning HTTP 201 and unique ID. | FastAPI Backend | **Verified & Passing** |
| **AC-03** | User profile can be retrieved via `GET /api/users/{id}` returning HTTP 200. | FastAPI Backend | **Verified & Passing** |
| **AC-04** | Personal information can be created via `POST /api/users/{id}/personal-info` with strict 1:1 enforcement. | Backend / DB | **Verified & Passing** |
| **AC-05** | Attempting to create duplicate personal info for the same user returns HTTP 400. | Backend / DB | **Verified & Passing** |
| **AC-06** | Personal information can be partially updated via `PUT /api/users/{id}/personal-info`. | Backend / DB | **Verified & Passing** |
| **AC-07** | Multiple experiences can be created and retrieved in chronological order. | Backend / DB | **Verified & Passing** |
| **AC-08** | Setting experience `end_date < start_date` triggers an HTTP 422 validation error. | Schemas / Validation | **Verified & Passing** |
| **AC-09** | Ongoing experiences with `end_date = null` are fully supported and serialized. | Schemas / DB | **Verified & Passing** |
| **AC-10** | Non-existent user or experience requests return HTTP 404 with structured error envelopes. | Error Handling | **Verified & Passing** |
| **AC-11** | Interactive Swagger (`/docs`) and ReDoc (`/redoc`) accurately document all endpoints and schemas. | Documentation | **Verified & Passing** |
| **AC-12** | Complete automated test suite passes with zero failures. | Testing Suite | **Verified (15/15 Passing)** |
| **AC-13** | External form labels are correctly mapped to canonical fields with $> 85\%$ accuracy on benchmark forms. | Vector / Semantic | *Planned (Phase 3)* |
| **AC-14** | Experiences are ranked by semantic relevance to a job description. | Vector / Semantic | *Planned (Phase 3)* |
| **AC-15** | Browser extension detects form fields and populates values only upon user confirmation. | Frontend / Extension | *Planned (Phase 4)* |

---

## 21. Risks, Limitations & Mitigation Strategies

| Risk / Limitation | Severity | Likelihood | Impact | Mitigation Strategy |
| :--- | :---: | :---: | :--- | :--- |
| **Ambiguous or Obfuscated Field Names** (e.g., `id="f_782"`, label missing) | High | High | Semantic matcher cannot decipher meaning from empty or random text. | Use surrounding DOM context: examine ancestor `<div>` text, placeholder attributes, preceding headings, and sibling elements. |
| **Incorrect Semantic Mapping** | High | Medium | Inaccurate data filled into high-stakes application forms. | Enforce strict human-in-the-loop confirmation. Require user review before DOM insertion; display color-coded confidence indicators. |
| **Dynamic Single-Page App Forms (SPAs)** (React/Vue multi-step forms) | Medium | High | Fields render dynamically after initial page load or re-render on step changes. | Implement DOM `MutationObserver` in extension content script to detect dynamically inserted form elements. |
| **Shadow DOM & Iframe Isolation** | Medium | Medium | Content script cannot directly access inputs inside cross-origin iframes. | Detect iframes and request user permission to inject helper script into frame context where allowed by browser security. |
| **CAPTCHA & Bot Detection Mechanisms** | Low | High | Site blocks extension or flags automated interaction. | Magic Fill does not automate form submissions or network requests; it simulates native user keystrokes/events (`input`, `change`) only after click. |
| **AI Inference Latency** | Medium | Low | High-latency embedding generation delays form overlay rendering. | Cache embeddings of canonical profile fields; use lightweight, quantized Sentence Transformer models (e.g., `all-MiniLM-L6-v2` ONNX runtime). |
| **Sensitive Data Exposure** | Critical | Low | Accidental leakage of national ID or personal data in logs. | Mask sensitive fields in logs; enforce strict `.gitignore` rules preventing `.env` commits; use HTTPS for all extension-to-backend traffic. |

---

## 22. Security & Privacy

1. **Zero Secret Leakage:** The application configuration loads all credentials from `.env`, which is strictly excluded in `.gitignore`. Production database credentials are never committed.
2. **Sanitized Database Exceptions:** SQLAlchemy exceptions are captured globally by `sqlalchemy_exception_handler`, preventing raw SQL statements, database table names, or connection strings from leaking to clients.
3. **Payload Sanitization:** Pydantic models forbid undeclared extra attributes (`extra="forbid"`), preventing mass-assignment vulnerabilities.
4. **Local Data Primacy:** Profile information is used strictly for form completion and is never shared with third-party tracking services or analytics aggregators.

---

## 23. Development Roadmap

```text
Phase 1: Backend & Relational Foundation [CURRENT - COMPLETE]
├── FastAPI REST API architecture, Pydantic schemas, and Service layer (Muazam)
├── Relational DB models (users, personal_info, experiences) & relationships (Adeel)
└── Automated Pytest suite (15 tests) & Swagger documentation (Muazam)
                            │
                            ▼
Phase 2: Database Hardening & Frontend Dashboard [UPCOMING]
├── PostgreSQL production configuration & Alembic migrations (Adeel)
└── Web UI for User profile and experience management (Hussnain)
                            │
                            ▼
Phase 3: Vector Database & Semantic Intelligence [PLANNED]
├── Embedding generation pipeline & vector database setup (Qasim)
├── Semantic field mapping engine (Qasim + Muazam)
└── Contextual experience relevance algorithm (Qasim + Muazam)
                            │
                            ▼
Phase 4: Browser Extension & Form Integration [PLANNED]
├── Manifest V3 extension with DOM form detection (Hussnain)
├── Floating suggestion card & confidence badge overlay (Hussnain)
└── Autofill execution engine with user confirmation (Hussnain)
                            │
                            ▼
Phase 5: System Integration & Final Evaluation [PLANNED]
├── End-to-end integration across Extension, Backend, Relational, and Vector tiers
├── Benchmark field matching evaluation across 50 real-world job portals
└── University Capstone Defense & Documentation
```

---

## 24. JIRA Requirement & Task Mapping

The PRD requirements are broken down into work packages mapped to team member responsibilities for JIRA sprint planning:

### Backend Epics & Tasks (Muazam Ali)
- **`BACK-01`**: Initialize FastAPI project structure and lifespan configuration. *(Completed)*
- **`BACK-02`**: Implement Pydantic v2 schemas with cross-field date validation. *(Completed)*
- **`BACK-03`**: Build User entity CRUD endpoints (`POST /api/users`, `GET /api/users/{id}`). *(Completed)*
- **`BACK-04`**: Build Personal Information endpoints with 1:1 constraint enforcement. *(Completed)*
- **`BACK-05`**: Build Experience endpoints supporting multiple roles and active statuses. *(Completed)*
- **`BACK-06`**: Implement centralized exception handling and standardized response envelope. *(Completed)*
- **`BACK-07`**: Develop automated Pytest suite with in-memory SQLite fixture. *(Completed)*
- **`BACK-08`**: Configure OpenAPI metadata, tags, and Swagger UI. *(Completed)*
- **`BACK-09`**: Expose API contract for vector database field matching integration. *(Planned)*
- **`BACK-10`**: Expose API contract for contextual experience relevance ranking. *(Planned)*

### Database Epics & Tasks (Adeel)
- **`DB-01`**: Design relational schema for `users`, `personal_info`, and `experiences`. *(Completed)*
- **`DB-02`**: Implement SQLAlchemy 2.0 ORM models with cascading delete rules. *(Completed)*
- **`DB-03`**: Configure PostgreSQL engine with SQLite compatibility fallback. *(Completed)*
- **`DB-04`**: Setup Alembic database migration environment. *(Planned)*
- **`DB-05`**: Implement PostgreSQL connection pooling and production index optimization. *(Planned)*
- **`DB-06`**: Perform relational database concurrency and integrity testing. *(Planned)*

### Vector & Semantic Memory Epics & Tasks (Qasim)
- **`VECTOR-01`**: Evaluate and select vector database framework (FAISS / pgvector / Chroma). *(Planned)*
- **`VECTOR-02`**: Benchmark and integrate Sentence Transformer embedding model. *(Planned)*
- **`VECTOR-03`**: Implement vector storage and indexing for profile attributes. *(Planned)*
- **`VECTOR-04`**: Build semantic similarity search engine for external form field mapping. *(Planned)*
- **`VECTOR-05`**: Develop contextual relevance scoring algorithm for experiences against job descriptions. *(Planned)*
- **`VECTOR-06`**: Conduct accuracy evaluation on benchmark job portal forms. *(Planned)*

### Frontend & Form Epics & Tasks (Hussnain)
- **`FRONT-01`**: Initialize frontend framework for user profile management dashboard. *(Planned)*
- **`FRONT-02`**: Build personal information viewing and editing interface. *(Planned)*
- **`FRONT-03`**: Build experience portfolio management interface. *(Planned)*
- **`FRONT-04`**: Construct Chromium Manifest V3 browser extension skeleton. *(Planned)*
- **`FRONT-05`**: Implement DOM input element parser and label extraction engine. *(Planned)*
- **`FRONT-06`**: Build floating suggestion overlay with confidence indicator badges. *(Planned)*
- **`FRONT-07`**: Implement human-in-the-loop confirmation modal (Accept / Reject / Edit). *(Planned)*
- **`FRONT-08`**: Implement DOM input simulation and autofill execution. *(Planned)*

---

## 25. Current vs. Future Development Status

| Component / Feature | Responsible | Status | Location in Codebase |
| :--- | :--- | :---: | :--- |
| **FastAPI REST Application** | Muazam Ali | **Implemented** | `backend/app/main.py` |
| **User Management API** | Muazam Ali | **Implemented** | `backend/app/routers/users.py`, `user_service.py` |
| **Personal Info API (1:1)** | Muazam Ali | **Implemented** | `backend/app/routers/personal_info.py`, `personal_info_service.py` |
| **Experience API (1:N)** | Muazam Ali | **Implemented** | `backend/app/routers/experiences.py`, `experience_service.py` |
| **Pydantic Validation Schemas** | Muazam Ali | **Implemented** | `backend/app/schemas/` |
| **Centralized Error Handling** | Muazam Ali | **Implemented** | `backend/app/exceptions.py`, `backend/app/main.py` |
| **Swagger / OpenAPI Documentation** | Muazam Ali | **Implemented** | `/docs`, `/redoc`, `/openapi.json` |
| **Automated Pytest Suite (15 Tests)** | Muazam Ali | **Implemented** | `backend/tests/` (15/15 passing) |
| **Relational ORM Models** | Adeel | **Implemented** | `backend/app/database/models.py` |
| **Dual Database Engine (Postgres/SQLite)** | Adeel | **Implemented** | `backend/app/database/database.py` |
| **Alembic Database Migrations** | Adeel | **Planned** | Not yet created in repository |
| **Vector Database Setup (FAISS/pgvector)** | Qasim | **Planned** | Not yet created in repository |
| **Embedding Generation Pipeline** | Qasim | **Planned** | Not yet created in repository |
| **Semantic Field Mapping Engine** | Qasim | **Planned** | Not yet created in repository |
| **Contextual Experience Relevance** | Qasim | **Planned** | Not yet created in repository |
| **User Web Dashboard** | Hussnain | **Planned** | Not yet created in repository |
| **Chromium Browser Extension** | Hussnain | **Planned** | Not yet created in repository |
| **DOM Field Detection & Autofill** | Hussnain | **Planned** | Not yet created in repository |
| **User Confirmation Overlay** | Hussnain | **Planned** | Not yet created in repository |
| **Memory Delta Update Prompt** | All Members | **Planned** | Not yet created in repository |

---

## 26. Testing Strategy

### 26.1 Backend Testing (Implemented)
- **Framework:** Pytest + Starlette/HTTPX TestClient.
- **Isolation:** Tests execute against an isolated, in-memory SQLite database (`sqlite:///:memory:`) utilizing `StaticPool` to avoid inter-test pollution and eliminate external database dependencies.
- **Coverage Areas:**
  1. System health check (`/health`), OpenAPI schema generation, and Swagger availability.
  2. User registration and retrieval.
  3. Personal Information creation, 1:1 uniqueness validation, and partial updating.
  4. Multi-experience portfolio creation, chronological retrieval, and partial updating.
  5. Cross-field validation (rejection of `end_date < start_date`).
  6. HTTP 404 and HTTP 422 error response structure verification.

### 26.2 Vector Retrieval Testing (Planned - Phase 3)
- **Benchmark Dataset:** 100 labeled external form fields collected from top job platforms.
- **Evaluation Metrics:**
  - **Top-1 Accuracy:** Percentage of fields where the correct canonical field is the highest-ranked vector match.
  - **MRR (Mean Reciprocal Rank):** Average reciprocal rank of the correct canonical attribute.
  - **Relevance Precision@3:** Precision of recommended experiences against human-evaluated relevance standards.

### 26.3 Frontend & Form Integration Testing (Planned - Phase 4)
- **Framework:** Playwright or Cypress for end-to-end browser automation.
- **Test Matrix:** Google Forms, Workday application forms, Greenhouse application forms, and Taleo portals.
- **Verification:** Ensure values are correctly written to input fields and that native change events (`input`, `change`) fire properly to trigger client-side validation scripts.

---

## 27. GitHub & Contribution Workflow

To maintain code quality and transparent accountability across team members, the following Git branching and commit guidelines are established:

### 27.1 Branching Strategy
- `main`: Production-ready, fully tested releases only.
- `develop`: Shared integration branch.
- Feature branches named by domain:
  - `feat/backend-<task-name>` (Muazam Ali)
  - `feat/db-<task-name>` (Adeel)
  - `feat/vector-<task-name>` (Qasim)
  - `feat/frontend-<task-name>` (Hussnain)

### 27.2 Commit Message Standards
Team members must use conventional commits with descriptive scopes:
```text
feat(backend): implement experience update endpoint and date validation
feat(db): configure postgresql connection pooling and alembic migrations
feat(vector): initialize sentence transformer embedding model
feat(frontend): create DOM input parser for chromium extension
test(backend): add unit tests for duplicate personal info rejection
docs(prd): update functional requirements for semantic field mapping
```

---

## 28. Conclusion

This Product Requirements Document establishes the comprehensive technical and operational baseline for **Magic Fill (Personal Information Memory & Intelligent Form Completion)**. 

The project has achieved its **Phase 1 milestone**: a fully functional, tested, and documented FastAPI backend architecture with relational persistence (Users, Personal Information, and Multiple Experiences) that adheres to enterprise design patterns and is decoupled from future AI layers. 

With this foundation secured, subsequent phases will systematically layer on the **Vector Database & Semantic Intelligence** (Qasim), **Database Hardening** (Adeel), and the **Chromium Extension & User Dashboard** (Hussnain) to deliver a seamless, privacy-respecting, and intelligent form autofill platform.
