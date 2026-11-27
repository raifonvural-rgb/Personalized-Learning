# Design Decisions

## Purpose

This document records significant architectural, pedagogical
and methodological decisions, their rationale and limitations.

Decisions must be preserved across development sessions.
Changes to previous decisions must be explicitly documented.

## DD-001 - Teacher-Controlled Artificial Intelligence

Status: Accepted.

Decision:

AI assists teachers in designing educational materials.
It does not independently determine educational objectives,
student requirements or final material suitability.

Rationale:

Special education requires individualized professional
judgment. AI-generated content may contain errors or
inappropriate assumptions.

The teacher retains final educational authority.

## DD-002 - Mandatory Automatic Verification

Status: Accepted.

Decision:

Personalized educational materials must undergo automatic
verification against teacher-defined student requirements.

Requirements that cannot be reliably verified automatically
must be explicitly flagged for teacher assessment.

Rationale:

AI generation alone cannot guarantee educational suitability.

Automatic verification provides an additional protection
mechanism but does not replace teacher judgment.

## DD-003 - Separation of Educational Concepts

Status: Accepted.

Decision:

The following concepts must remain logically distinct:

- Learning outcome
- Teaching method
- Teaching strategy
- Educational material
- Learning activity
- Student-specific personalization
- Assessment
- Teacher approval

Rationale:

A single learning outcome may be taught using multiple
methods, materials and activities.

Separating these concepts supports reuse, personalization
and systematic evaluation.

## DD-004 - Central Student Profile Schema

Status: Implemented.

Decision:

Maintain a centralized and structured student profile
rather than independent student settings for each activity.

Rationale:

Individual student requirements should be reusable across
activities and educational materials.

A central schema supports consistent validation and
future extensions.

Current implementation:

11 sections and 100 fields.

## DD-005 - Educational Diagnoses Are Descriptive

Status: Implemented.

Decision:

Educational diagnoses must not automatically generate
student restrictions or instructional requirements.

Rationale:

Students with the same diagnosis may have substantially
different abilities, preferences and educational needs.

Personalization must be based primarily on individual
characteristics identified by the teacher.

## DD-006 - Support Structured and Free-Text Requirements

Status: Accepted.

Decision:

Student profiles must support structured fields and
additional teacher-defined free-text requirements.

Rationale:

A predefined schema cannot anticipate every individual
educational requirement.

Free-text requirements provide flexibility but may
require manual assessment when automatic verification
is unreliable.

## DD-007 - Separate Validation from Approval

Status: Implemented for existing activities.

Decision:

Automatic validation and teacher approval must remain
separate operations.

Rationale:

Passing automatic validation does not establish complete
pedagogical suitability.

The teacher must retain the authority to accept,
revise or reject a material.

## DD-008 - Reusable Visual Material Library

Status: Implemented.

Decision:

Visual assets must be maintained independently of
individual educational activities.

Supported sources:

- Parametric SVG objects
- Teacher-uploaded photographic images
- AI-generated educational images

Rationale:

Reusable visual assets reduce duplication, support
consistent presentation and minimize repeated AI requests.

## DD-009 - Parametric SVG and Photographic Materials

Status: Implemented.

Decision:

Support both parametric SVG objects and photographic
images rather than selecting only one visual format.

Rationale:

Some students may benefit from simplified visual
representations, while others may benefit from
realistic representations.

SVG materials also support deterministic customization.

Photographic suitability may require additional
teacher assessment.

## DD-010 - Separate Image Generation from Storage

Status: Implemented.

Decision:

The AI image generation provider must remain independent
of image persistence, activity construction and approval.

Rationale:

This separation improves modularity, testability and
future provider replacement.

Image generation must not automatically publish an
asset into the approved Visual Library.

## DD-011 - Explicit Visual Material Approval

Status: Implemented.

Decision:

Teacher-uploaded and AI-generated photographic images
must enter temporary review storage before approval.

The teacher may approve or reject each image.

Rationale:

Generated or uploaded images may be unsuitable,
incorrect or visually distracting.

Approval establishes eligibility for reuse, not universal
suitability for every student.

## DD-012 - Two Independent Approval Levels

Status: Accepted and demonstrated in teacher workflows.

Decision:

Distinguish between:

1. Approval of a reusable visual asset.
2. Approval of a personalized educational activity.

Rationale:

A generally acceptable visual asset may still conflict
with the requirements of a particular student.

Limitations:

Complete production student-access enforcement has
not yet been verified.

## DD-013 - Content-Based Image Deduplication

Status: Implemented and tested.

Decision:

Store one master copy of identical normalized image
content using content-based hashing.

Duplicate uploads must preserve the original asset
and its provenance.

Rationale:

This reduces unnecessary storage and prevents
duplicate catalog entries.

Limitation:

Content-based deduplication does not identify visually
similar images with different underlying content.

## DD-014 - Preserve AI Generation Provenance

Status: Implemented and tested.

Decision:

Record the image source, generation model and generation
prompt for approved AI-generated assets.

Rationale:

Provenance supports traceability, research evaluation
and investigation of generation failures.

Limitation:

Preserving the prompt and model does not guarantee
exact reproduction of a generated image.

## DD-015 - Deterministic Numerical Correctness

Status: Accepted; quantity activity implementation pending.

Decision:

For number-quantity correspondence activities,
AI generates individual visual objects.

The application determines the exact number of
displayed object instances.

Example:

To represent the number 5, display five instances
of an approved individual object.

Do not rely on an AI-generated image containing
exactly five objects.

Rationale:

Generative image models may produce incorrect
object counts.

Deterministic composition separates mathematical
correctness from visual generation.

This guarantees the number of rendered instances,
provided the approved asset represents one object.

Teacher verification of the individual asset remains
necessary.

## DD-016 - Separate Number Recognition and Quantity

Status: Accepted; new activity implementation pending.

Decision:

Numerical symbol recognition and number-quantity
correspondence must be separate activity types.

Rationale:

Recognizing a numerical symbol does not necessarily
demonstrate understanding of its represented quantity.

Both number-to-quantity and quantity-to-number
interactions should be supported.

## DD-017 - Mandatory MEB Teaching Method Coverage

Status: Accepted; comprehensive implementation pending.

Decision:

All 35 identified MEB mathematics teaching methods
constitute a mandatory coverage baseline.

The platform may exceed this baseline but must
not silently omit any identified method.

Rationale:

Educational coverage must be driven by pedagogical
requirements rather than software convenience.

Methods requiring physical materials, natural settings
or human interaction may require teacher-mediated
or offline support.

Coverage must distinguish planned, implemented and
tested functionality.

## DD-018 - Teaching Method Designer

Status: Planned.

Decision:

Introduce a dedicated teaching-method design layer.

It should support:

- Instructional task steps
- Prompt types and intensity
- Prompt timing and fading
- Independent response opportunities
- Error correction strategies
- Reinforcement
- Mastery criteria
- Learning progression
- Generalization
- Progress tracking

Rationale:

Teaching methods cannot be represented adequately
by visual presentation settings alone.

## DD-019 - Independent Activity Copying

Status: Accepted; implementation pending.

Decision:

A teacher must be able to copy an activity designed
for one student to another student.

The copied activity must be independently editable.

The original activity must remain unchanged.

The copied activity must undergo validation against
the target student's profile and require teacher approval.

Rationale:

Activity reuse improves teacher efficiency without
compromising individual personalization.

## DD-020 - External Credential Management

Status: Implemented and tested.

Decision:

API credentials and Flask session secrets must remain
outside version-controlled source code.

The OpenAI API key is loaded through a protected
external configuration file.

Rationale:

Credentials must not be exposed through source code,
Git history or development documentation.

Limitation:

Restricted file permissions protect local access but
do not constitute encrypted secret storage.

## DD-021 - Privacy Boundary for External AI

Status: Accepted.

Decision:

External image generation requires only the teacher's
visual description, not the student's complete profile.

Teachers must not include identifiable student
information in external generation requests.

Rationale:

Minimize unnecessary disclosure of sensitive
student information.

Limitation:

A teacher-facing privacy warning does not guarantee
that submitted descriptions contain no personal data.

## DD-022 - GitHub as the Development Reference

Status: In progress.

Decision:

Maintain application source code and project
documentation in GitHub.

Exclude credentials, student records, private
runtime data, uploaded images and local backups.

Rationale:

Repository-based development reduces repeated source
code transfers into ChatGPT conversations.

It also supports version history, reproducibility,
collaboration and development continuity.

Limitation:

GitHub does not contain uncommitted local changes.

The repository is currently public and requires
careful review before publication.

## DD-023 - Incremental Verified Development

Status: Accepted.

Decision:

Develop the platform through small, controlled
and independently verifiable changes.

Inspect existing implementation before modifying it.

Preserve working functionality and perform
appropriate regression checks.

Rationale:

Incremental development reduces the risk of
introducing uncontrolled changes into a growing
research prototype.

## DD-024 - Distinguish Evidence from Proposals

Status: Accepted.

Decision:

Documentation and research publications must
distinguish between:

- Implemented functionality
- Automated test results
- Manual demonstrations
- Architectural proposals
- Research hypotheses
- Known limitations

Rationale:

A proposed architecture or successful demonstration
must not be presented as comprehensive empirical
validation.

## DD-025 - Development and Production Separation

Status: Accepted.

Decision:

The current Flask application is a research
and development prototype.

Production deployment requires additional
security, authorization, privacy, concurrency
and operational controls.

Rationale:

Successful local functional testing does not
establish production readiness.


## DD-026 - Quantity Representation Activities

Status: Accepted and implemented.

Decision:

Support two independent instructional directions:

- Number to Quantity (Rakamdan miktara)
- Quantity to Number (Miktardan rakama)

Generate object groups through deterministic replication
of a single approved visual asset.

Support quantities from zero to nine, configurable
answer choices, and grid, horizontal and vertical
object arrangements.

Do not assign an official MEB learning outcome code
until authoritative curriculum mapping is verified.

## DD-027 - Educational Counting Reinforcement

Status: Accepted and implemented.

Decision:

Quantity animation must reinforce counting rather
than merely provide a success reward.

Individual objects are sequentially enlarged and
highlighted, optionally synchronized with Turkish
spoken counting.

Spoken counting and quantity animation are independently
configurable by the teacher.

Counting reinforcement occurs after the correct answer
to avoid revealing the answer prematurely.

Respect browser reduced-motion preferences.

## DD-028 - Student Learning Dashboard

Status: Accepted. Implementation pending.

Decision:

Replace the original standalone /student demonstration
with a personalized Student Learning Dashboard
(Ogrenci Ogrenme Paneli).

The planned route architecture is:

- /student
  Student Learning Dashboard.

- /student/activity/<activity_id>
  Execution of an assigned and approved activity.

- /student/preview
  Authorized teacher preview.

Do not introduce a separate /student/demo route.

Preserve existing interactive learning functionality
by integrating it into the activity execution interface.

Historical demonstration code remains available
through Git version history.

Rationale:

Provide a single, clear entry point for students
and prevent bypassing the personalized learning workflow.

The dashboard must itself respect individual student
requirements.

Dependencies:

- Secure student identification
- Teacher and student authorization
- Activity assignment management
- Student-specific activity access control

## DD-029 - Approval, Assignment and Execution Separation

Status: Accepted. Assignment implementation pending.

Decision:

Distinguish three independent concepts:

1. Approval: the teacher determines that an activity
   is suitable for a particular student.

2. Assignment: the teacher determines that the student
   should undertake an approved activity.

3. Execution: the student performs an assigned activity.

Approval does not automatically imply assignment.

Students must access only their own assigned and
approved activities.

Teacher previews must not generate student performance
records.

Historical performance evidence must remain available
when activities are revised.

AI-generated learning recommendations must remain
subject to teacher approval.

## DD-030 - Proportionate Development Verification

Status: Accepted.

Decision:

Prioritize functional development through small,
controlled implementation increments.

Perform targeted verification after meaningful changes
and broader regression checks at milestone boundaries.

Retain important regression tests in reusable test files.

Avoid repetitive ad hoc testing that provides little
additional evidence or delays functional development.

Safety-critical validation, student isolation and
teacher approval controls require rigorous verification.

This decision refines DD-023 without removing its
incremental development principles.

## Decision Maintenance

New significant decisions must receive a unique identifier.

Existing decisions should not be silently overwritten.

If a decision changes, record:

- The previous decision
- The revised decision
- The reason for the change
- Affected components
- Required verification

Implementation status must be updated as evidence
becomes available.


## DD-031 — Teacher-Assisted Student Identification

Status: Accepted and implemented in Step 43.

The teacher opens the Student Learning Dashboard on each
student's computer and selects the appropriate student from
the existing student profile list.

The teacher initiates the session using Ogrenmeye Basla
and terminates it using Oturumu Sonlandir.

Passwords, PINs, device pairing and separate student accounts
are intentionally excluded from the current supervised prototype.

The learning_student_id session key is independent of
the teacher's active_student_id session key.

Separate browser sessions are intended to support simultaneous
student use. Multiple tabs in the same browser share session
cookies and are not independent student environments.

Multi-student operation requires further verification.

This decision simplifies supervised classroom operation.
It does not provide production-grade identity verification,
authentication or authorization.


## DD-032 — Single Active Activity Assignment

**Status update — 2026-11-27:** The single-assignment
restriction remains part of the Step 44 implementation,
but is superseded as a future architectural requirement
by DD-036. Multiple-assignment support is planned for
Step 46.


Date: 2026-11-25

Status: Implemented

A teacher assigns one approved activity at a time
to an individual student.

Assignment is independent of activity approval.

Assigning another activity replaces the current assignment.

The student does not select activities from a queue.
The assigned activity opens automatically when the
learning session starts.

This decision minimizes student interaction complexity
and preserves teacher control.

Scheduling, activity queues and automatic sequencing
are outside the current implementation scope.

## DD-033 — Assignment-Bound Learning Sessions

Date: 2026-11-25

Status: Implemented

Learning sessions are associated with unique assignment
identifiers rather than student identifiers alone.

Session termination removes an assignment only when
its identifier matches the learning session.

This prevents an older learning session from deleting
a newer assignment.

Approved activities and teacher context remain unchanged.

Invalid learning sessions are cleared without silently
deleting the underlying assignment.

An already rendered activity is not continuously
monitored for assignment changes.

## DD-034 — Deferred Comprehensive Verification

Date: 2026-11-25

Status: Adopted

Extends DD-030.

Incremental development will prioritize implementation
with proportionate verification.

Basic compilation, integration checks and targeted
functional tests will continue.

Additional test scenarios will be recorded in
TEST_RESULTS.md for later execution.

Comprehensive regression, security, accessibility
and usability verification will be conducted
before project completion.

Blocking failures and essential integrity controls
must still be addressed during development.


---

## DD-035 — Persistent Assignment-Bound Performance Sessions

Status: Implemented in Step 45.3.

An assignment may have multiple historical learning
sessions, but at most one active learning session.

Performance records are stored in SQLite. Existing
student profiles, activities, assignments and visual
material storage remain unchanged.

Session creation and lifecycle events are transactional.
Repeated compatible session creation requests reuse
the existing active session.

Historical performance records survive assignment
removal and session termination.

The normal session lifecycle has been verified.
Comprehensive verification remains outstanding.

---

# Design Decisions Following Teacher Consultation

Date: 2026-11-27

The following decisions define the planned development
direction following consultation with a special
education teacher.

They are not claims of implemented functionality.

## DD-036 — Multiple Enabled Assignments

A teacher may enable multiple approved activities
for an individual student.

This supersedes the single-assignment restriction
defined in DD-032.

Only one assignment is executed at a time within
the student's learning sequence.

## DD-037 — Teacher-Controlled Assignment Sequence

The teacher determines the order in which enabled
assignments are presented to the student.

## DD-038 — Sequential Student Progression

The student advances to the next assigned activity
using the Sonraki button without returning to the
student dashboard.

## DD-039 — Successful Completion Before Advancement

The student cannot advance to the next assignment
until the current activity satisfies its instructional
completion criteria.

Exhausting answer alternatives alone does not
constitute successful completion.

The teacher may interrupt or terminate an activity
without recording successful completion.

## DD-040 — Reusable Feedback Library

Animated feedback characters and associated audio
and text shall be implemented as reusable components.

## DD-041 — Student-Specific Feedback

Feedback shall be configurable according to individual
student characteristics, preferences and sensory needs.

## DD-042 — Encouraging Incorrect-Answer Feedback

Incorrect-answer feedback shall be supportive,
non-punitive and encouraging.

Humor shall not ridicule or embarrass the student.

## DD-043 — Independent Feedback Modalities

Animation, written feedback, spoken feedback and
additional sound effects shall be independently
configurable.

## DD-044 — Feedback Performance Events

Feedback and reinforcement presentations shall be
recorded as performance events.

Presentation of a stimulus does not establish that
the student attended to it or that it functioned
as an effective reinforcer.

## DD-045 — Discovery Through Trial and Error

The student shall be permitted to discover the correct
answer by trying all available alternatives.

The system shall acknowledge discovery of the correct
answer rather than interrupting the exercise before
the correct answer is selected.

## DD-046 — Repetition Following Discovery

When the student discovers the correct answer after
trying all alternatives, the system shall acknowledge
the discovery and repeat the same exercise.

The learning target remains unchanged.

The answer alternatives shall be reordered.

## DD-047 — Preservation of Attempts and Rounds

All student responses, exercise rounds and restarts
shall be preserved in the performance history.

Restarting an exercise shall not erase earlier
incorrect or correct responses.

## DD-048 — Completion Is Not Mastery

Successful activity completion shall not automatically
be interpreted as mastery of an educational achievement.

Initial first-attempt correctness, subsequent
correctness and correctness following repetition
shall be distinguished.

## DD-049 — Three Feedback Categories

The system shall support three feedback categories:

A. Successful completion:
   Celebrating star.

   Aferin! Doğru cevabı buldun!

B. Incorrect answer:
   Encouraging turtle.

   Bir daha deneyelim. Haydi, tekrar bak!

C. Discovery followed by repetition:
   Thinking robot.

   Evet, doğru cevabı buldun! Şimdi bir daha
   deneyelim. Bakalım ilk seferde bulabilecek misin?

## DD-050 — First-Attempt Success Following Discovery

Following discovery through elimination, the student
must answer correctly on the first attempt of a
subsequent round before advancement is permitted.

If a subsequent round includes an incorrect response,
another round is required after the correct answer
is discovered.

This rule shall be implemented through a reusable
activity execution mechanism.

## DD-051 — Animated Feedback Characters

Feedback characters shall perform actual movements.

Initial characters:

- Star: gentle jumping and celebration.
- Turtle: head movement, scratching its head and nodding.
- Robot: thoughtful head movement, illuminated light
  bulb and discovery gesture.

Animated SVG with CSS or JavaScript is the preferred
initial implementation approach.

## DD-052 — Written and Spoken Turkish Feedback

Feedback messages shall be displayed as written text
and read aloud in Turkish by default.

## DD-053 — Synchronized Multimodal Feedback

Animation, displayed text and spoken feedback shall
be coordinated as a single feedback presentation.

## DD-054 — Persistent Written Feedback

Written feedback shall remain visible after animation
and speech completion until the next relevant
interaction or exercise transition.

## DD-055 — Teacher-Customizable Feedback Messages

The teacher shall be able to customize the written
and spoken feedback messages.

## DD-056 — Configurable Feedback Presentation

The teacher shall be able to configure:

- Animation enabled or disabled.
- Written feedback enabled or disabled.
- Spoken feedback enabled or disabled.
- Additional sound effects enabled or disabled.
- Animation speed and duration.
- Speaking speed and volume.

Student-level defaults and activity-specific
overrides shall be supported.

## DD-057 — Sensory Suitability and Teacher Approval

Feedback shall avoid excessive, sudden or potentially
distressing sensory stimulation.

Feedback configurations shall undergo automatic
verification against known student-specific constraints.

Uncertain verification results shall be explicitly
reported to the teacher.

The teacher retains final approval authority.

## DD-058 — Uninterrupted Feedback Presentation

Normal exercise progression shall not interrupt
the feedback message.

The Sonraki button shall become available only after
successful completion and the required feedback
presentation.

Speech or animation failures must not permanently
block progression.

Teacher interruption remains available.
