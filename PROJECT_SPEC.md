# Project Specification — SpiderPi Edge-AI Autonomous Robotics System

This document defines clear project requirements and acceptance criteria. It was used as the working specification for development, including AI-assisted coding under human review (requirements → implementation → testing → revision).

## 1. Goals

1. Build a hexapod robotics platform that performs autonomous navigation in a constrained demo environment.
2. Run computer vision / ML perception on the edge (onboard or local edge compute) for object and hazard-related detection.
3. Stream or expose monitoring data through an IoT workflow for remote situational awareness.
4. Deliver a competition-ready demonstration integrating perception, locomotion, and monitoring.

## 2. Scope

### In scope

- Vision pipeline using OpenCV + TensorFlow for real-time detection cues
- Motion control using inverse kinematics / gait logic for stable locomotion
- Sensor-to-IoT monitoring path for environmental / operational status
- End-to-end demo scenario suitable for hackathon judging

### Out of scope

- Full SLAM mapping stack
- Multi-robot coordination
- Production-hardened cybersecurity certification

## 3. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | System shall detect at least one target object/hazard class via onboard vision in real time. |
| FR-2 | System shall execute autonomous locomotion commands based on perception or planned demo path. |
| FR-3 | System shall maintain stable hexapod gait during navigation on the demo surface. |
| FR-4 | System shall publish monitoring status (e.g., detection event, robot state, or sensor reading) to an IoT/monitoring endpoint or dashboard. |
| FR-5 | Operator shall be able to start/stop the demo safely. |

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | Perception loop shall be responsive enough for live demo interaction (target: interactive real-time, not offline batch). |
| NFR-2 | Code and configuration shall be reproducible on the SpiderPi / project hardware profile. |
| NFR-3 | Critical control actions shall remain under human oversight during demos. |
| NFR-4 | Documentation shall explain setup, run steps, and known limits. |

## 5. Constraints

- Hardware: SpiderPi hexapod + available camera/sensors
- Software: Python, OpenCV, TensorFlow
- Environment: hackathon/demo floor conditions (lighting variance, limited space)
- Timeline: competition delivery schedule for IoT Data Hackathon 2026

## 6. Acceptance criteria

The project is accepted when all of the following are true:

1. Live demo shows vision-based detection during robot operation.
2. Robot completes an autonomous navigation segment without operator teleoperation for the full path.
3. IoT/monitoring path shows at least one live status or event update during the demo.
4. README documents stack, role, and how to run.
5. Failure modes (lost detection, stuck gait) have a documented recovery/stop procedure.

## 7. Test plan

| Test | Procedure | Pass condition |
|---|---|---|
| T1 Vision | Present target object/hazard in camera view | Detection event triggers consistently |
| T2 Locomotion | Run autonomous segment on demo surface | Robot completes segment without tip-over |
| T3 Integration | Run full perception + motion demo | Both subsystems operate in one session |
| T4 IoT path | Trigger monitoring event during run | Remote/local monitor receives update |
| T5 Safety stop | Issue stop during motion | Robot halts promptly |

## 8. AI-assisted development workflow

1. Write/update this specification (human-owned requirements).
2. Use AI coding tools to draft modules (vision glue code, control helpers, IoT publishers) against the requirements above.
3. Human review of logic, hardware assumptions, and safety-critical paths.
4. Run T1–T5; revise spec or code where tests fail.
5. Freeze demo configuration for competition.

## 9. Success metric (competition)

Deliver a coherent Edge-AI robotics demonstration judged competitive in the Robotics category — achieved: **1st place, IoT Data Hackathon 2026 (Hong Kong)**.
