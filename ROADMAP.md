# Development Roadmap

Last updated: 2026-11-24

## 1. Long-Term Objective

Develop a comprehensive teacher-controlled, AI-assisted
personalized educational platform for special education.

The initial educational focus is mathematics instruction
for students with autism.

The architecture should support future expansion to
additional learning domains and individual educational needs.

## 2. Current Foundation

The following infrastructure has been established:

- Central student profile management
- Educational diagnosis recording
- Activity design and personalization
- Automatic student-specific validation
- Teacher review and approval
- Activity persistence
- Interactive student activities
- Reusable Visual Library
- Parametric SVG materials
- Teacher-uploaded photographic materials
- AI-generated visual materials
- Image provenance and deduplication
- External credential management

GitHub integration and quantity representation activities
have been implemented.

## 3. Immediate Development Priorities

### RM-001 - GitHub Integration

Status: Completed.

Objectives:

- Complete project documentation
- Establish dependency specifications
- Review source code for publication
- Commit source code and documentation
- Synchronize the Linux server with GitHub
- Verify ChatGPT repository access
- Establish a repeatable development workflow

### RM-002 - Quantity Representation Activity

Status: Implemented; core functional verification completed.
Development milestone: Step 41.

Objectives:

- Introduce a separate quantity representation activity
- Support number-to-quantity interactions
- Support quantity-to-number interactions
- Reuse approved visual assets
- Control object counts deterministically
- Support configurable numerical ranges
- Support configurable answer choices
- Support student-specific visual arrangements
- Support spoken counting
- Support optional animation
- Integrate validation and teacher approval

Existing numerical recognition activities must remain
functional and independent.

## 4. Activity Management and Reuse

### RM-003 - Independent Activity Copying

Status: Planned.

Objectives:

- Copy an existing activity to another student
- Preserve the original activity
- Create an independently editable configuration
- Revalidate against the target student profile
- Require a new teacher approval decision

### RM-004 - Activity Management Improvements

Status: Proposed.

Objectives:

- Activity search and filtering
- Organization by learning outcome
- Organization by teaching method
- Activity version history
- Reusable activity templates
- Clear approval and validation status indicators

## 5. Teaching Method Infrastructure

### RM-005 - Teaching Method Designer

Status: Planned.

Objectives:

- Select an appropriate teaching method
- Define instructional task steps
- Configure prompting strategies
- Configure prompt intensity
- Configure prompt timing
- Configure prompt fading
- Define independent response opportunities
- Define error correction strategies
- Configure reinforcement
- Define mastery criteria
- Support learning progression
- Support generalization

Teaching methods must remain distinct from
learning outcomes and visual material settings.

### RM-006 - MEB Teaching Method Coverage

Status: Mandatory requirement; implementation ongoing.

All 35 identified MEB mathematics teaching methods
must be represented in the development roadmap.

For each method:

- Define its pedagogical requirements
- Identify required software capabilities
- Identify teacher-mediated requirements
- Design appropriate activity examples
- Implement relevant functionality
- Define verification procedures
- Record demonstrated coverage
- Identify remaining limitations

Methods requiring physical objects, natural settings
or human interaction must not be omitted merely
because they cannot be fully implemented digitally.

See MEB_METHOD_COVERAGE.md.

## 6. Student Progress and Assessment

### RM-007 - Student Performance Recording

Status: Planned.

Proposed capabilities:

- Record student responses
- Record correct and incorrect responses
- Record response times
- Record assistance and prompting levels
- Record independent task completion
- Record repeated attempts

### RM-008 - Learning Progress Assessment

Status: Planned.

Proposed capabilities:

- Learning outcome progress
- Individual performance history
- Mastery assessment
- Identification of persistent difficulties
- Teacher-facing progress reports
- Comparison across instructional sessions

### RM-009 - Teacher-Controlled Adaptation

Status: Proposed.

The platform may recommend activity adjustments
based on observed student performance.

Potential recommendations:

- Change difficulty
- Adjust numerical range
- Adjust answer choices
- Modify prompting
- Modify reinforcement
- Repeat or advance instructional steps

Recommendations must remain subject to teacher review.

The platform must not autonomously redefine
student educational objectives.

## 7. Multimodal Educational Materials

### RM-010 - Enhanced Visual Materials

Status: Partially implemented.

Existing capabilities:

- SVG visual materials
- Photographic materials
- AI-generated images
- Visual material approval and reuse

Potential extensions:

- Additional parametric objects
- Configurable object sizes
- Configurable line thickness
- Configurable visual complexity
- Background customization
- Visual contrast customization
- Asset categorization
- Visual asset search

### RM-011 - Audio Materials

Status: Proposed.

Objectives:

- Configurable spoken instructions
- Adjustable speech rate
- Configurable repetition
- Reusable audio materials
- Teacher-approved generated audio
- Student-specific auditory suitability checks

### RM-012 - Video and Animation Materials

Status: Proposed.

Objectives:

- Educational animations
- Video modeling materials
- Step-by-step instructional sequences
- Teacher-controlled playback
- Student-specific duration and pacing
- Teacher review and approval

### RM-013 - Integrated Educational Material Packages

Status: Planned.

Combine appropriate visual, auditory, interactive
and teacher-mediated materials into structured
personalized instructional packages.

Each package must support validation and
final teacher approval.

## 8. Validation Infrastructure

### RM-014 - Expanded Automatic Verification

Status: Partially implemented.

Objectives:

- Expand structured student requirement checks
- Verify numerical correctness
- Verify activity configuration consistency
- Verify visual requirements where reliable
- Verify auditory requirements where reliable
- Identify unresolved free-text requirements
- Explain validation findings
- Explicitly flag uncertain verification results

Automatic verification must never be represented
as a substitute for professional teacher assessment.

### RM-015 - Validation Traceability

Status: Partially implemented.

Objectives:

- Preserve validation results
- Associate results with activity versions
- Identify changes requiring revalidation
- Record teacher decisions
- Support investigation of validation failures

## 9. Student Profile Improvements

### RM-016 - Duplicate Student Record Prevention

Status: Planned.

Objectives:

- Detect potentially duplicate records
- Request explicit teacher confirmation
- Preserve unique student identifiers
- Allow legitimate students with identical names

### RM-017 - Profile Evolution

Status: Proposed.

Objectives:

- Support changes in student requirements over time
- Track relevant profile revisions
- Identify affected approved activities
- Determine when revalidation is required

## 10. Research and Evaluation

### RM-018 - Structured Material Representation

Status: Research objective.

Develop and evaluate a structured representation
of personalized instructional materials.

Investigate relationships among:

- Student requirements
- Learning outcomes
- Teaching methods
- Material configurations
- Validation findings
- Teacher decisions
- Student performance

### RM-019 - Evaluation of AI-Assisted Design

Status: Planned.

Potential evaluation dimensions:

- Material correctness
- Student-specific suitability
- Teacher workload
- Material design efficiency
- Validation effectiveness
- Teacher acceptance
- Reusability
- Educational method coverage

Research conclusions must be supported by
appropriate empirical evidence.

### RM-020 - Teacher Training Support

Status: Planned.

Support teacher training through:

- Example student profiles
- Guided material design
- Individual and group activities
- Material evaluation exercises
- Teacher-mediated simulations
- Reflective assessment

Use synthetic or appropriately authorized data
for training and research demonstrations.

## 11. Production Readiness

### RM-021 - Authentication and Authorization

Status: Pending.

Requirements:

- Teacher authentication
- Student authentication or controlled access
- Teacher-specific resource ownership
- Role-based authorization
- Student data isolation
- Enforcement of activity release decisions

### RM-022 - Application Security and Privacy

Status: Pending.

Requirements:

- CSRF protection
- Secure session management
- API usage limits
- Input validation
- Personal data protection
- Secure credential management
- Appropriate logging
- Data retention policies

### RM-023 - Reliability and Persistence

Status: Pending.

Requirements:

- Server-side concurrency protection
- Safe concurrent image approval
- Abandoned temporary file cleanup
- Backup and recovery procedures
- Storage integrity checks
- Evaluation of database-backed persistence

### RM-024 - Production Deployment

Status: Pending.

Requirements:

- Production WSGI server
- Disabled Flask debug mode
- HTTPS configuration
- Secure reverse proxy configuration
- Restricted service permissions
- Operational monitoring
- Deployment documentation

The current prototype must not be considered
production-ready.


### RM-025 - Student Learning Dashboard

Status: Planned. Mandatory development milestone.

Objectives:

- Replace the standalone /student demonstration
- Provide a personalized Student Learning Dashboard
- Display assigned and approved activities
- Support starting and continuing activities
- Display completion status
- Personalize dashboard presentation
- Respect individual student requirements

Planned routes:

- /student
- /student/activity/<activity_id>
- /student/preview

No separate demonstration route will be maintained.

Dependencies: RM-021 and RM-026.

See DD-028.

### RM-026 - Teacher-Controlled Activity Assignment

Status: Planned. Mandatory development milestone.

Objectives:

- Separate activity approval from assignment
- Assign approved activities to individual students
- Support assignment ordering
- Support assignment withdrawal
- Prevent unauthorized activity access
- Track assignment completion status
- Preserve teacher control over learning progression

Teacher previews must not affect student performance
or assignment completion records.

See DD-029.

### RM-027 - Continued Activity Suitability

Status: Planned.

Objectives:

- Detect student profile changes after activity approval
- Identify activities requiring revalidation
- Detect missing visual asset files
- Detect modifications to previously approved assets
- Prevent delivery of invalid or unsuitable activities
- Require renewed teacher review when necessary

Existing launch-time integrity and asset approval
checks provide an initial foundation.

## 12. Development Sequence

Immediate sequence:

1. Complete GitHub integration (completed).
2. Implement quantity representation activities (implemented).
3. Implement student identification and access control.
4. Implement teacher-controlled activity assignment.
5. Replace /student with the Student Learning Dashboard.
6. Implement student performance and completion recording.
7. Implement teacher-facing progress monitoring.
8. Strengthen continued activity suitability verification.
9. Review activity management and reuse requirements.
10. Design the Teaching Method Designer.
11. Establish systematic MEB method implementation.
12. Expand assessment and teacher-controlled adaptation.
13. Extend multimodal material capabilities.
14. Conduct research evaluation.
15. Complete remaining production readiness requirements.

This sequence is provisional and may be revised
based on educational priorities and research findings.

Security and privacy requirements must be addressed
before any deployment involving real users or student data.

## 13. Roadmap Maintenance

Each roadmap item has a persistent identifier.

New requirements must be recorded rather than
left exclusively in conversation history.

Status changes must reflect actual implementation
and verification evidence.

Detailed implementation progress is maintained in
DEVELOPMENT_STATUS.md.

Architectural rationale is maintained in
DESIGN_DECISIONS.md.

Verification evidence is maintained in
TEST_RESULTS.md.
