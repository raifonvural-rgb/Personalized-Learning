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
