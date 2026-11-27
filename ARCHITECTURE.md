# System Architecture

## 1. Architectural Overview

Personalized Learning is a modular Flask-based research
prototype for teacher-controlled personalized education.

The architecture separates student requirements, educational
activity design, material generation, validation, teacher
approval and activity presentation.

## 2. Logical Architecture

    Teacher Interface
           |
           v
    Student Profile + Learning Outcome
           |
           v
    Activity Designer <---- Visual Material Library
           |
           v
    Student-Specific Activity Configuration
           |
           v
    Automatic Validation
           |
           v
    Teacher Review and Decision
           |
           v
    Activity Persistence and Presentation

## 3. Application Entry Point

### app.py

Responsibilities:

- Flask application initialization
- Blueprint registration
- Application routing
- Learning outcome definitions
- Teacher and student interface coordination

The Flask session secret is maintained outside source code.

## 4. Student Profile Subsystem

### Components

| File | Responsibility |
|---|---|
| student_profiles.py | Central student profile schema |
| profile_storage.py | Persistent student profile management |
| profile_api.py | Student profile API |
| active_student_api.py | Active student management |
| templates/student_profile.html | Profile editing interface |
| static/js/student_profile.js | Profile interface behavior |
| static/css/student_profile.css | Profile interface styling |

### Profile Structure

The current schema contains 11 sections and 100 fields.

1. General information
2. Educational diagnoses
3. Visual characteristics
4. Auditory characteristics
5. Motor characteristics
6. Language and communication
7. Attention and learning
8. Motivation and feedback
9. Sensory and emotional characteristics
10. Academic characteristics
11. Additional individual requirements

Educational diagnoses provide descriptive information.
They must not automatically determine student restrictions.

Personalization must primarily reflect individual requirements
identified by the teacher.

## 5. Activity Design Subsystem

| File | Responsibility |
|---|---|
| activity_models.py | Activity configuration models |
| activity_request.py | Activity request processing |
| activity_builder.py | Activity construction |
| activity_options.py | Activity configuration options |
| activity_layouts.py | Activity presentation layouts |
| activity_templates.py | Activity template definitions |
| activity_validation.py | Student-specific validation |
| activity_validation_record.py | Validation record management |
| activity_fingerprint.py | Activity configuration fingerprinting |
| activity_storage.py | Persistent activity management |

### Current Activity Capabilities

- Numerical symbol recognition
- Configurable answer choices
- Configurable numerical ranges
- Visual object selection
- Written and auditory instructions
- Interactive number tracing
- Visual and auditory feedback
- Optional correct-answer animation
- Teacher preview
- Validation and teacher approval

Quantity representation will be introduced as a separate
activity type.

## 6. Visual Material Library

The Visual Library provides reusable educational assets
independently of individual activity configurations.

### Components

| File or directory | Responsibility |
|---|---|
| visual_library/routes.py | Visual Library API and routes |
| visual_library/photo_storage.py | Image persistence and deduplication |
| visual_library/image_generator.py | Independent AI image provider |
| visual_library/color_safety.py | Student-specific color checks |
| visual_library/renderers/ | Parametric SVG renderers |
| visual_library/catalog/ | SVG visual assets |
| templates/visual_library.html | Teacher-facing Visual Library |

### Supported Material Sources

1. Parametric SVG objects
2. Teacher-uploaded photographs
3. AI-generated educational images

### AI Image Generation Workflow

    Teacher Description
           |
           v
    AI Image Generation Provider
           |
           v
    Temporary Image Storage
           |
           v
    Teacher Preview
           |
           +---- Reject ---> Temporary File Cleanup
           |
           +---- Approve --> Duplicate Detection
                                    |
                                    v
                            Permanent Visual Library

AI-generated images are never automatically approved.

Image provenance includes the source, generation model
and generation prompt where applicable.

Approved images can be reused by multiple activities.

## 7. Numerical Correctness

For quantity representation, AI should generate an individual
visual object rather than a complete image containing a
requested number of objects.

The application will control the exact number of displayed
object instances.

This design separates visual generation from mathematical
correctness and reduces unnecessary AI generation requests.

Quantity representation is planned, not yet implemented
as an independent activity type.

## 8. Validation and Teacher Authority

Automatic verification is a mandatory architectural component.

Validation must distinguish between:

- Requirements that can be verified automatically
- Detected conflicts or warnings
- Requirements requiring teacher assessment

Uncertain verification results must be explicitly reported.

The teacher retains final authority to accept, revise
or reject an educational material.

Visual Library approval and personalized activity approval
are separate decisions.

## 9. Persistence

The current prototype uses JSON-based persistence.

| Runtime resource | Purpose |
|---|---|
| data/students.json | Student profiles |
| data/activities.json | Saved activity configurations |
| data/visual_assets.json | Approved visual asset catalog |
| visual_library/uploads/ | Permanent photographic assets |
| visual_library/pending/ | Temporary image review assets |

These runtime resources are excluded from Git.

Image deduplication uses content-based hashing.

Database-backed persistence may be considered in a later
development phase.

## 10. External AI Integration

The image generation provider is isolated from storage,
activity construction and teacher approval.

Current default configuration:

- Provider: OpenAI
- Model: gpt-image-1-mini
- Image size: 1024 x 1024
- Quality: medium

The model can be configured through OPENAI_IMAGE_MODEL.

The API key is supplied through the OPENAI_API_KEY
environment variable.

The provider receives the teacher's image description.
It does not require access to the student profile.

Teachers must not include identifiable student information
in external AI generation requests.

## 11. Application Startup

The start.sh script loads protected external configuration
and starts the Flask development application.

External configuration location:

    ~/.config/autism_material_demo/openai.env

Required configuration file permissions: 600.

The development server binds to:

    127.0.0.1:6000


## 11A. Quantity Representation Architecture

Implemented in Step 41.

The activity architecture supports three interactive
activity types:

- find_digit
- number_to_quantity
- quantity_to_number

Quantity representation remains independent of
digit recognition.

### Quantity Activity Components

| Module | Responsibility |
|---|---|
| quantity_activity_models.py | Configuration and constraints |
| quantity_activity_builder.py | Deterministic activity generation |
| quantity_activity_integrity.py | Canonical draft verification |
| quantity_activity_validation.py | Quantity-specific suitability checks |
| student_activity_validation.py | Shared student requirement checks |
| visual_asset_validation.py | Shared visual asset approval checks |
| activity_integrity.py | Activity integrity dispatch |
| activity_validation_dispatcher.py | Student validation dispatch |
| activity_request.py | Activity request processing |
| activity_storage.py | Shared persistence and approval |

### Activity Processing Pipeline

    Teacher Configuration
            |
            v
    Activity Request Dispatcher
            |
            v
    Activity-Specific Model and Builder
            |
            v
    Deterministic Activity Draft
            |
            v
    Integrity Verification
            |
            v
    Student-Specific Validation
            |
            v
    Teacher Review and Approval
            |
            v
    Launch-Time Integrity Verification
            |
            v
    Interactive Student Activity

### Deterministic Object Representation

Each object group references a single approved
visual asset through multiple object instances.

Object quantities are generated programmatically,
rather than relying on generative AI to produce
images containing an exact number of objects.

Zero is represented by an empty object group.

### Student-Specific Quantity Validation

Quantity-specific checks include:

- Total simultaneously displayed object count
- Animation suitability
- Moving image suitability
- Spoken counting suitability
- Object arrangement review
- Visual complexity review
- Reinforcement suitability review
- Academic suitability review

Uncertain checks require teacher assessment.

### Interactive Counting Reinforcement

After a correct response, the student interface
can sequentially enlarge and highlight individual
objects while optionally counting aloud in Turkish.

Animation and spoken counting are independently
configurable.

The implementation respects browser reduced-motion
preferences.

### Current Student Routes

- /student: original standalone demonstration
- /student?preview=1: teacher preview
- /student?activity_id=...: approved activity execution

These routes describe the current prototype,
not the intended final student architecture.

### Remaining Limitations

- Production authentication and authorization
  are not yet implemented.
- Post-approval student profile changes are not
  automatically checked at activity launch.
- Asset content changes under the same identifier
  are not detected.
- Missing image files are not comprehensively
  checked before delivery.
- Teacher preview uses browser session storage.
- Official MEB learning outcome mapping for quantity
  activities remains pending.

## 11B. Planned Student Learning Architecture

Status: Accepted design; implementation pending.

The standalone student demonstration will be replaced
by a personalized Student Learning Dashboard.

Planned routes:

    /student
        Student Learning Dashboard

    /student/activity/<activity_id>
        Assigned and approved activity execution

    /student/preview
        Authorized teacher preview

No separate demonstration route will be maintained.

Existing interactive activity execution functionality
will be reused.

### Planned Learning Lifecycle

    Activity Design
           |
           v
    Automatic Suitability Validation
           |
           v
    Teacher Approval
           |
           v
    Teacher Assignment
           |
           v
    Student Learning Dashboard
           |
           v
    Activity Execution
           |
           v
    Performance Recording
           |
           v
    Teacher Progress Monitoring

Approval and assignment are separate operations.

Only assigned and approved activities may be
accessible to the authorized student.

Teacher previews must not generate student
performance records.

Dashboard presentation must respect individual
student requirements.

See DD-028, DD-029, RM-025 and RM-026.

## 12. Planned Architectural Extensions

- Student Learning Dashboard
- Teacher-controlled activity assignment
- Continued activity suitability verification
- Teaching Method Designer
- Structured prompting and prompt fading
- Learning progression and mastery assessment
- Student progress tracking
- Independent activity copying between students
- Target-student revalidation
- Multimodal educational material generation
- Comprehensive MEB teaching method coverage

These are planned extensions, not claims of completed
implementation.

## 13. Production Deployment Requirements

The current application is a development prototype.

Outstanding production requirements include:

- Teacher authentication and authorization
- Student access authorization
- Teacher-specific resource ownership
- Student data isolation
- CSRF protection
- API usage limits
- Server-side concurrency protection
- Abandoned temporary file cleanup
- Production WSGI server
- Disabled Flask debug mode
- Secure deployment configuration

Teacher preview functionality has been demonstrated.
Complete production student-access enforcement has not
yet been verified.

## 14. Architecture Maintenance

This document must be updated when significant architectural
changes are introduced.

Detailed design decisions are maintained in DESIGN_DECISIONS.md.

Current implementation progress is maintained in
DEVELOPMENT_STATUS.md.

The source code remains the authoritative reference for
actual implementation behavior.


## Step 43 — Student Learning Session Architecture

The student-facing learning environment is separated from the
teacher's activity design and preview environment.

### Session contexts

- active_student_id: teacher-selected student context.
- learning_student_id: student learning session context.

Both contexts reuse existing student profile identifiers.
Starting or terminating a learning session does not modify
the teacher's active student selection.

### Routes

| Route | Responsibility |
|---|---|
| /student | Student Learning Dashboard |
| /student/preview?preview=1 | Teacher draft preview |
| /student/preview?activity_id=ID | Teacher approved activity preview |
| /api/learning-session | Read, initiate or terminate learning session |

The learning_session_api module provides GET, POST and DELETE
operations for learning session management.

The student dashboard uses existing student profiles.
No separate student identity database is introduced.

Teacher preview remains separate from actual student learning.
The existing educational activity execution engine is preserved.

The future /student/activity/<activity_id> route is reserved
for assigned activity execution and is not implemented yet.

Session separation is not authentication or full authorization.
The current architecture supports supervised prototype use only.


## Step 44 — Teacher-Controlled Activity Assignment

The architecture now distinguishes four independent concepts:

1. Activity design and configuration.
2. Teacher validation and approval.
3. Teacher-controlled activity assignment.
4. Student learning execution.

### Assignment Layer

New modules:

- assignment_storage.py
- assignment_api.py

Assignments are stored separately from approved activities
in data/assignments.json.

Each student can have one current assignment.
Each assignment has a unique identifier, student identifier,
activity identifier and assignment timestamp.

Assignment storage uses file locking and atomic replacement.

### Learning Session Layer

The learning session maintains:

- learning_student_id
- learning_assignment_id

These are independent of active_student_id,
which belongs to the teacher context.

### Execution Routes

Teacher preview:

- /student/preview
- /api/student-activities/<activity_id>

Student learning:

- /student/activity/<activity_id>
- /api/learning-activity/<activity_id>

Assignment management:

- GET /api/activity-assignment
- POST /api/activity-assignment

Student session management:

- GET /api/learning-session
- POST /api/learning-session
- DELETE /api/learning-session

The existing student activity rendering engine is reused
for teacher preview and actual learning.

The server determines the execution mode.

Student execution requires a matching learning session,
current assignment, student ownership, approved activity
and successful activity integrity verification.

Session termination clears only the matching assignment.
Approved activities remain available for future use.

Invalid activity execution clears the learning session
before redirecting to the student dashboard.

The invalid assignment remains available for teacher review.

Production authentication, comprehensive concurrency
verification and performance recording remain outstanding.


---

## Step 45.3 — Persistent Performance Architecture

Status: Implemented.
Date: 2026-11-27.

### Architectural Separation

The performance subsystem separates three levels:

1. Raw observations and performance events.
2. Derived performance indicators and progress analysis.
3. Educational interpretation and recommendations.

Step 45.3 establishes the persistence infrastructure
for the first level.

Detailed response recording, derived indicators and
educational interpretation remain future work.

The teacher retains final educational decision authority.

### Implemented Components

| Component | Responsibility |
|---|---|
| performance_database.py | SQLite schema, connections and transactions |
| performance_models.py | Session and event data models |
| performance_storage.py | Transactional persistence and retrieval |
| performance_event_validation.py | Event payload validation |
| performance_lifecycle.py | Assignment-bound performance lifecycle |
| learning_session_api.py | Browser learning session integration |
| app.py | Database initialization and execution authorization |

### Persistence Architecture

Existing JSON-based storage remains unchanged.

- Student profiles: JSON.
- Activity configurations: JSON.
- Current assignments: JSON.
- Visual material library: existing storage.
- Performance sessions and events: SQLite.

The performance database is stored at:

    data/performance.db

Runtime data remains excluded from GitHub.

SQLite uses foreign key enforcement, WAL mode,
transactional writes and a schema version identifier.

### Performance Data Model

The principal database tables are:

- schema_metadata
- learning_sessions
- performance_events

A learning session identifies:

- Student.
- Assignment.
- Activity.
- Achievement, when available.
- Learning mode.
- Activity configuration snapshot.
- Start and end timestamps.
- Session status.
- Termination reason.

Performance events identify:

- Event.
- Learning session.
- Question, when applicable.
- Attempt, when applicable.
- Event sequence number.
- Event type.
- Occurrence timestamp.
- Recording timestamp.
- Event source.
- Structured payload.
- Event schema version.

Performance events are append-only through the
application storage interface.

Database-level enforcement of event immutability
has not yet been implemented.

### Learning Modes

The data model supports:

- COMPUTER_BASED
- TEACHER_ASSISTED
- TEACHER_LED

The currently integrated execution workflow uses
COMPUTER_BASED mode.

Teacher-assisted and teacher-led observation
interfaces remain future work.

### Session Lifecycle

Supported session states:

- ACTIVE
- COMPLETED
- TERMINATED
- INTERRUPTED

An assignment may have multiple historical learning
sessions but at most one active learning session.

This invariant is enforced using a partial unique
SQLite index.

Compatible repeated session creation requests reuse
the existing active session.

Session creation and its SESSION_STARTED event
are recorded transactionally.

Session finalization and its SESSION_ENDED event
are recorded transactionally.

Historical performance records are retained after
assignment removal.

### Event Architecture

The event model supports:

- SESSION_STARTED
- SESSION_ENDED
- QUESTION_PRESENTED
- QUESTION_COMPLETED
- INSTRUCTION_DELIVERED
- INSTRUCTION_REPEATED
- RESPONSE_SUBMITTED
- PROMPT_DELIVERED
- ASSISTANCE_PROVIDED
- FEEDBACK_DELIVERED
- REINFORCEMENT_DELIVERED
- TEACHER_OBSERVATION_RECORDED

At this milestone, session lifecycle events are
integrated into actual student execution.

Detailed question, response and feedback recording
is not yet integrated into the student interface.

### Observation and Interpretation Boundaries

Every response attempt must eventually be preserved.

Unknown assistance must not be interpreted as
independent performance.

Correctness, completion and mastery are distinct
educational concepts.

Teacher previews must not generate actual student
performance records.

Presentation of feedback does not prove student
attention or reinforcement effectiveness.

### Current Architectural Limitations

- JSON assignment storage and SQLite performance
  storage do not share a single atomic transaction.
- Exclusive browser ownership of a learning session
  is not yet enforced.
- Production authentication and authorization
  remain outstanding.
- Browser closure is not automatically interpreted
  as session interruption.
- Comprehensive concurrency, recovery and regression
  verification remains outstanding.

---

## Step 46 — Teacher-Controlled Multiple Assignment Architecture

Status: Planned.
Source: Teacher consultation, 2026-11-27.

### Motivation

The teacher requires the ability to enable several
approved activities for a student in advance.

The student should complete these activities
sequentially without returning to the dashboard
between activities.

This requirement supersedes the single-assignment
restriction of Step 44 and DD-032.

The existing Step 44 implementation remains
unchanged until Step 46 is implemented.

### Proposed Logical Architecture

    Student
        |
        +-- Ordered learning sequence
                |
                +-- Assignment 1
                |       +-- Learning sessions
                |               +-- Performance events
                |
                +-- Assignment 2
                |       +-- Learning sessions
                |               +-- Performance events
                |
                +-- Assignment N
                        +-- Learning sessions
                                +-- Performance events

The learning sequence is a proposed logical
abstraction. Its physical persistence model
will be determined during Step 46.1.

### Teacher Responsibilities

The teacher shall be able to:

- Select approved student activities.
- Enable and disable individual assignments.
- Determine their execution order.
- Add activities to the learning sequence.
- Review assignment completion status.
- Assign previously completed activities again.

Assignment management must not modify or delete
the original approved activity configuration.

### Student Execution

Only one assignment shall be executed at a time
within a student's learning sequence.

The student shall advance using Sonraki after
successful completion of the current activity.

The last activity shall provide an appropriate
learning sequence completion interface.

The student shall not independently bypass
an unfinished assignment.

Teacher interruption remains available and
must not be interpreted as successful completion.

### Shared Exercise Execution Mechanism

The progression mechanism shall be reusable across
multiple-choice activity types.

The initial implementation shall support:

- Digit recognition.
- Number-to-quantity representation.
- Quantity-to-number representation.

Future compatible activities should reuse the
same execution mechanism.

### Exercise Rounds and Discovery

An exercise may contain multiple rounds.

Each round may contain multiple response attempts.

The student may continue selecting alternatives
until the correct answer is discovered.

If the correct answer is discovered after trying
all alternatives:

1. Acknowledge discovery of the correct answer.
2. Present encouraging discovery feedback.
3. Preserve all previous attempts.
4. Repeat the same learning target.
5. Reorder the answer alternatives.
6. Require first-attempt correctness in a
   subsequent round before advancement.

If a repetition round contains an incorrect
response, successful discovery is acknowledged,
but another round is required.

The exact presentation and attempt history must
be retained for subsequent performance analysis.

### Completion and Performance Interpretation

The architecture shall distinguish:

- Initial first-attempt correctness.
- Correctness after one or more incorrect attempts.
- Correctness discovered through elimination.
- First-attempt correctness following repetition.
- Successful exercise completion.
- Assignment completion.
- Learning sequence completion.

None of these observations alone establishes
long-term educational mastery.

---

## Step 47 — Multimodal Feedback Architecture

Status: Planned.
Source: Teacher consultation, 2026-11-27.

### Reusable Feedback Library

Feedback shall be represented as reusable components,
independent of individual activity implementations.

The initial library shall contain three categories.

| Category | Character | Purpose |
|---|---|---|
| A | Celebrating star | Successful completion |
| B | Encouraging turtle | Incorrect response |
| C | Thinking robot | Discovery followed by repetition |

### Initial Character Behavior

Celebrating star:

- Gentle jumping.
- Raised arms.
- Smiling celebration.

Encouraging turtle:

- Gentle head movement.
- Scratching its head.
- Encouraging smile and nod.

Thinking robot:

- Thoughtful head movement.
- Illuminated light bulb.
- Discovery gesture.
- Encouraging smile.

### Feedback Presentation Components

Each feedback presentation may contain:

- Animated character.
- Written Turkish message.
- Spoken Turkish message.
- Optional additional sound effect.

The preferred initial implementation is animated
SVG using CSS or JavaScript, combined with the
existing browser speech synthesis mechanism.

The final implementation technology will be
confirmed during Step 47.

### Presentation Lifecycle

    Response evaluation
        |
        +-- Select feedback category
        |
        +-- Apply student-specific configuration
        |
        +-- Display written feedback
        |
        +-- Start character animation
        |
        +-- Read message aloud
        |
        +-- Complete feedback presentation
        |
        +-- Continue, repeat or enable Sonraki

Animation and speech shall be coordinated.

Written feedback shall remain visible until
the next relevant interaction or transition.

Normal progression shall not interrupt the
feedback presentation.

Speech or animation failures must not permanently
block activity progression.

Teacher interruption must remain available.

### Student-Specific Configuration

The architecture shall support:

- Student-level feedback defaults.
- Activity-specific overrides.
- Character selection.
- Teacher-defined messages.
- Animation enablement, speed and duration.
- Written feedback enablement.
- Spoken feedback enablement.
- Speaking speed and volume.
- Optional sound effects.

Automatic verification shall evaluate known
student-specific sensory constraints.

Uncertain suitability shall be reported explicitly.

Final approval remains with the teacher.

### Performance Integration

The actual feedback configuration and presentation
events shall be recorded in the performance history.

The system shall distinguish attempted presentation
from confirmed application-level completion.

It shall not infer that the student heard,
understood or attended to the feedback solely
from successful software execution.

### Educational Method Coverage

The multiple-assignment, repetition and feedback
architecture provides reusable infrastructure
for future teaching method implementations.

These capabilities do not establish complete
implementation of any MEB teaching method.

The mandatory coverage baseline of all 35
identified teaching methods remains unchanged.

---

## Current Development Continuation

1. Complete Step 45.3 documentation and checkpoint.
2. Implement Step 46 multiple-assignment execution.
3. Implement Step 47 multimodal feedback.
4. Resume Step 45.4 detailed performance recording.
5. Develop performance history and progress analysis.
6. Conduct comprehensive deferred verification.
