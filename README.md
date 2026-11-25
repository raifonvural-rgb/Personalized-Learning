# Personalized Learning

## Project Overview

Personalized Learning is a teacher-controlled, AI-assisted
educational material design platform for special education,
with an initial focus on students with autism.

The platform supports the design, personalization, verification,
approval and delivery of educational activities based on
individual student requirements.

## Core Design Principles

- Teacher-controlled personalization
- Student-specific educational requirements
- Curriculum-aligned learning outcomes
- Mandatory automatic material verification
- Explicit reporting of uncertain verification results
- Final approval authority remains with the teacher
- Reusable educational materials
- Privacy and security by design
- Separation of AI generation from educational decisions

## Current Capabilities

- Detailed student profile management
- Educational diagnosis recording
- Student-specific activity configuration
- Number recognition activities
- Number-to-quantity representation activities
- Quantity-to-number representation activities
- Deterministic visual object group generation
- Configurable numerical ranges and answer choices
- Personalized visual object arrangements
- Optional Turkish spoken counting
- Sequential individual object animation
- Quantity-specific student suitability validation
- Launch-time activity integrity verification
- Interactive number tracing
- Visual and auditory feedback
- Activity validation and teacher approval
- Activity persistence
- Parametric SVG visual materials
- Teacher-uploaded photographic materials
- AI-generated educational images
- Visual material review, approval and rejection
- Image deduplication and provenance tracking
- Reusable visual material library
- External API credential management

## Technology Stack

- Python
- Flask
- HTML, CSS and JavaScript
- JSON-based prototype persistence
- SVG and PNG visual materials
- Pillow image processing
- OpenAI Image Generation API
- Linux development environment
- Git and GitHub version control

## Educational Scope

The platform is designed to support the teaching methods
specified by the Turkish Ministry of National Education (MEB).

All 35 identified mathematics teaching methods constitute
a mandatory coverage baseline rather than an upper limit.

Implementation coverage is tracked separately in
MEB_METHOD_COVERAGE.md.

## Running the Development Application

After installing the required dependencies and configuring
the external OpenAI credentials, start the application with:

    ./start.sh

The development server listens on:

    http://127.0.0.1:6000

The current application is a research and development prototype,
not a production-ready deployment.

## Privacy and Security

Student records, saved personalized activities, uploaded images,
runtime data, credentials and local backups must not be committed
to this repository.

API credentials are stored outside the project directory.

Production deployment requires additional authentication,
authorization, privacy and concurrency controls.

## Project Documentation

- ARCHITECTURE.md
- DEVELOPMENT_STATUS.md
- DESIGN_DECISIONS.md
- ROADMAP.md
- MEB_METHOD_COVERAGE.md
- TEST_RESULTS.md

## Development Approach

Development proceeds incrementally through numbered milestones.

Each milestone should include:

1. Requirements and design decisions.
2. Implementation.
3. Verification and regression testing.
4. Documentation updates.
5. Version-controlled source code changes.

Demonstrated functionality must be distinguished from planned
features and unresolved limitations.

## Project Status

Research and development prototype under active development.

Completed development milestones include:

- Step 41: Quantity Representation Activities
- Step 42: GitHub Integration

Core quantity activity functionality has been
implemented and verified through automated checks
and manual browser demonstrations.

Further verification requirements and known
limitations are documented in TEST_RESULTS.md.

## Next Development Objectives

- Step 43: Student Identification and Access Control
- Teacher-controlled activity assignment
- Personalized Student Learning Dashboard
- Student performance recording
- Teacher-facing learning progress monitoring
- Continued activity suitability verification

The Student Learning Dashboard will replace the
original standalone /student demonstration.

Activity approval, assignment and execution will
remain separate operations.

The teacher retains final authority over activity
suitability and student learning progression.

These objectives describe planned functionality,
not completed implementation.


## Student Learning Dashboard — Step 43

The application now provides a dedicated Student Learning Dashboard
at /student.

For supervised learning, the teacher selects an existing student
profile and initiates the student's learning session.

The dashboard displays a personalized welcome message and an
Etkinliklerim section reserved for assigned learning activities.

Teacher activity previews are available through /student/preview
and remain separate from student learning sessions.

Activity assignment is planned for Step 44.

The current student identification mechanism is intended for
supervised prototype use and is not production authentication.


## Teacher-to-Student Learning Workflow

Implemented in Step 44.

1. Teacher selects a student.
2. Teacher designs a personalized activity.
3. The activity undergoes automatic validation.
4. Teacher reviews and approves the activity.
5. Teacher selects Ogrenciye Ata in the saved activity list.
6. Student identification is performed on the learning dashboard.
7. Ogrenmeye Basla automatically opens the assigned activity.
8. The student interacts with the activity.
9. Oturumu Sonlandir terminates the learning session.
10. The teacher can assign another approved activity.

Only one current assignment is maintained per student.

Ending a learning session removes the matching assignment
without deleting the approved activity.

Teacher preview remains independent of actual learning.

The current prototype uses teacher-assisted identification.
It is not a production-authenticated student platform.

Student performance recording and progress tracking
are planned for subsequent development.
