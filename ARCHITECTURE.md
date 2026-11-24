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

## 12. Planned Architectural Extensions

- Quantity representation activities
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
