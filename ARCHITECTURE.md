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
