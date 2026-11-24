# MEB Mathematics Teaching Method Coverage

Last updated: 2026-11-24

## 1. Purpose

This document establishes the mandatory pedagogical
coverage baseline for the Personalized Learning platform.

All 35 identified mathematics teaching methods must
be addressed by the platform.

The platform may exceed this baseline but must not
silently omit any identified method.

The Turkish method names are preserved as the primary
educational terminology.

## 2. Coverage Principles

A teaching method must not be considered implemented
merely because the platform contains potentially
relevant reusable software components.

Each method requires:

- Pedagogical requirement analysis
- Software requirement identification
- Teacher-mediated requirement identification
- Instructional activity examples
- Implementation where applicable
- Functional verification
- Pedagogical assessment
- Documentation of remaining limitations

Some methods require physical objects, human interaction
or natural learning environments.

The platform must support teachers in planning,
conducting and evaluating such methods rather than
excluding them because they cannot be fully digitized.

## 3. Coverage Status Definitions

| Status | Meaning |
|---|---|
| P | Planned; method-specific implementation not established |
| A | Pedagogical and software requirements analyzed |
| D | Method-specific design completed |
| I | Method-specific functionality implemented |
| V | Functionality verified through appropriate tests |
| E | Pedagogical effectiveness evaluated |

Delivery modes:

- Digital
- Teacher-mediated
- Physical or offline
- Hybrid

Delivery mode and implementation status are independent.

A method may require multiple delivery modes.

## 4. Group 1 - Direct and Systematic Instruction

Total methods: 9.

| ID | Teaching method | Status |
|---|---|---|
| MEB-01 | Doğrudan öğretim | P |
| MEB-02 | Basamaklandırılmış öğretim | P |
| MEB-03 | Gösterip yaptırma | P |
| MEB-04 | Yanlışsız öğretim | P |
| MEB-05 | Eşzamanlı ipucuyla öğretim | P |
| MEB-06 | Sabit bekleme süreli öğretim | P |
| MEB-07 | Artan bekleme süreli öğretim | P |
| MEB-08 | Aşamalı yardımla öğretim | P |
| MEB-09 | İpucunun giderek azaltılması | P |

### Candidate Software Capabilities

- Explicit instructional sequences
- Teacher demonstration
- Guided student practice
- Independent student practice
- Configurable prompts
- Prompt timing
- Fixed waiting intervals
- Increasing waiting intervals
- Graduated assistance
- Prompt fading
- Error prevention
- Error correction
- Response recording

### Important Design Requirement

Prompt timing, prompt intensity and prompt fading
must be independently configurable.

Different prompting methods must not be treated
as interchangeable.

## 5. Group 2 - Skill Acquisition and Cognitive Methods

Total methods: 7.

| ID | Teaching method | Status |
|---|---|---|
| MEB-10 | İleri zincirleme | P |
| MEB-11 | Geri zincirleme | P |
| MEB-12 | Tüm beceri yöntemi | P |
| MEB-13 | Model olma ve taklit | P |
| MEB-14 | Video modelle öğretim | P |
| MEB-15 | Bilişsel strateji öğretimi | P |
| MEB-16 | Problem çözme öğretimi | P |

### Candidate Software Capabilities

- Task analysis
- Ordered instructional steps
- Forward chaining
- Backward chaining
- Whole-task practice
- Demonstration and imitation
- Video modeling
- Cognitive strategy guidance
- Structured problem-solving activities
- Step-specific assistance
- Step-specific performance recording

### Important Design Requirement

Forward chaining, backward chaining and whole-task
instruction require distinct instructional execution
and assessment behavior.

A common task representation may support all three,
but their teaching procedures must remain distinct.

## 6. Group 3 - Multisensory and Material-Based Methods

Total methods: 8.

| ID | Teaching method | Status |
|---|---|---|
| MEB-17 | Somut-temsili-soyut öğretim (CRA) | P |
| MEB-18 | Çoklu duyulu öğretim | P |
| MEB-19 | Görsel destekli öğretim | P |
| MEB-20 | Dokunsal öğretim | P |
| MEB-21 | İşitsel destekli öğretim | P |
| MEB-22 | Matematik materyalleriyle öğretim | P |
| MEB-23 | Bilgisayar destekli öğretim | P |
| MEB-24 | Teknoloji destekli öğretim | P |

### Candidate Software Capabilities

- Concrete material activity instructions
- Representational visual materials
- Abstract mathematical symbols
- Transitions between representation levels
- Visual material selection
- Photographic and SVG materials
- Auditory instructions
- Spoken counting
- Interactive activities
- Teacher-guided tactile activities
- Physical material preparation instructions
- Multimodal material packages

### Existing Relevant Infrastructure

The following components have already been implemented:

- Reusable Visual Library
- Parametric SVG objects
- Photographic materials
- AI-generated visual materials
- Auditory feedback
- Interactive number tracing
- Computer-based number recognition activities
- Student-specific material validation

These components provide a foundation for several
methods in this group.

They do not establish complete method-specific
implementation or pedagogical effectiveness.

### Important Design Requirement

Digital representations must not automatically
be classified as concrete physical experiences.

Touchscreen interaction must not automatically
be classified as tactile instruction.

Physical and teacher-mediated activities must
be represented explicitly where required.

## 7. Group 4 - Naturalistic and Interactive Methods

Total methods: 7.

| ID | Teaching method | Status |
|---|---|---|
| MEB-25 | Oyun temelli öğretim | P |
| MEB-26 | Etkinlik temelli öğretim | P |
| MEB-27 | Doğal ortamda öğretim | P |
| MEB-28 | Fırsat öğretimi | P |
| MEB-29 | Keşfederek öğrenme | P |
| MEB-30 | Akran destekli öğretim | P |
| MEB-31 | İşbirlikli öğrenme | P |

### Candidate Software Capabilities

- Educational game design
- Structured learning activities
- Natural environment activity planning
- Everyday learning opportunity identification
- Guided exploration
- Peer-assisted activity planning
- Collaborative activity planning
- Individual and group task assignment
- Teacher observation forms
- Teacher-mediated performance recording

### Important Design Requirement

The platform must support educational experiences
outside the computer interface.

Peer-assisted and collaborative learning require
appropriate human interaction.

An individual computer activity must not be
classified as collaborative learning merely
because it contains interactive elements.

## 8. Group 5 - Academic and Applied Mathematics Methods

Total methods: 4.

| ID | Teaching method | Status |
|---|---|---|
| MEB-32 | Basamaklı matematik öğretimi | P |
| MEB-33 | Matematiksel problem çözme | P |
| MEB-34 | Günlük yaşam temelli matematik öğretimi | P |
| MEB-35 | İşlevsel matematik öğretimi | P |

### Candidate Software Capabilities

- Progressive mathematical task sequences
- Number recognition
- Number-quantity correspondence
- Counting activities
- Mathematical problem representation
- Everyday mathematics scenarios
- Shopping and money activities
- Time and calendar activities
- Measurement activities
- Functional mathematical tasks
- Generalization assessment

### Important Design Requirement

Mathematical correctness must be verified independently
of visual material generation.

Functional mathematics activities must be connected
to meaningful real-life educational objectives.

## 9. Coverage Summary

| Group | Required methods |
|---|---:|
| Direct and systematic instruction | 9 |
| Skill acquisition and cognitive methods | 7 |
| Multisensory and material-based methods | 8 |
| Naturalistic and interactive methods | 7 |
| Academic and applied mathematics methods | 4 |
| Total | 35 |

Initial formal method-specific coverage status:

- Planned: 35
- Formally analyzed: 0
- Method-specific design completed: 0
- Formally implemented: 0
- Formally verified: 0
- Pedagogically evaluated: 0

These initial counts do not imply that no relevant
software functionality exists.

They indicate that systematic method-specific
coverage assessment has not yet been completed.

## 10. Method-Specific Implementation Record

Create a separate implementation record for each
teaching method as development progresses.

Required fields:

- Method identifier
- Original Turkish method name
- Authoritative educational reference
- Pedagogical definition
- Instructional objectives
- Required teaching procedure
- Suitable learning outcomes
- Required student profile information
- Required educational materials
- Required software components
- Required teacher actions
- Delivery mode
- Personalization parameters
- Automatic verification requirements
- Teacher review requirements
- Example instructional activity
- Functional test cases
- Pedagogical evaluation criteria
- Implementation status
- Verification evidence
- Known limitations
- Relevant source files
- Relevant Git commits

## 11. Teaching Method Designer

The planned Teaching Method Designer will provide
shared infrastructure for implementing multiple
teaching methods.

Candidate configuration dimensions:

- Teaching method
- Learning outcome
- Instructional task sequence
- Demonstration
- Prompt type
- Prompt intensity
- Prompt timing
- Waiting duration
- Prompt fading
- Independent response opportunity
- Error prevention
- Error correction
- Reinforcement
- Mastery criteria
- Learning progression
- Generalization
- Teacher-mediated actions
- Student performance recording

Each teaching method will define its own appropriate
configuration and execution requirements.

Not every configuration dimension is applicable
to every method.

## 12. Automatic Verification and Teacher Approval

All personalized materials must undergo automatic
verification against individual student requirements.

Method-specific verification should also be introduced
where reliable deterministic checks are possible.

Examples of candidate checks:

- Correct instructional step ordering
- Valid prompt timing
- Correct object quantities
- Consistent answer choices
- Student-specific visual restrictions
- Student-specific auditory restrictions

Uncertain or unsupported checks must be reported
explicitly for teacher assessment.

Final approval remains with the teacher.

## 13. Future Extensions

Additional teaching methods may be introduced beyond
the mandatory baseline.

New methods must receive unique identifiers.

The original 35 methods must remain traceable even
if the classification or software architecture evolves.

## 14. Reference and Terminology Verification

The initial list preserves the 35 methods identified
during project planning.

The authoritative MEB source documents, publication
details and exact pedagogical definitions must be
recorded during method-specific requirement analysis.

The English group headings and candidate software
capabilities are project design classifications.

They must not be presented as official MEB
classifications without source verification.

## 15. Maintenance Rules

Update this document when:

- A teaching method is formally analyzed
- Method-specific requirements are established
- Relevant functionality is implemented
- Functional verification is completed
- Pedagogical evaluation is conducted
- A coverage gap is identified
- A new teaching method is introduced

Coverage claims must be supported by documented evidence.

No method may be removed from the mandatory baseline
without an explicit and documented scope decision.
