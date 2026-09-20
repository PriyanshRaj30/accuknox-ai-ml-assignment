

**1. GitHub:**[https://github.com/PriyanshRaj30/Aegis](https://github.com/PriyanshRaj30/Aegis)

**Aegis — Abuse-Aware API Gateway**

A production-inspired security-focused API gateway built entirely around Python/FastAPI. Aegis sits in front of backend services and makes real-time decisions on incoming requests based on authentication, rate-limit behaviour, burst patterns, and accumulated risk.

The most technically challenging part is the  **multi-layer abuse detection pipeline** : Redis-backed sliding-window rate limiting, an atomic Lua-scripted token bucket, per-second burst detection, and a behavioural risk engine with exponential score decay. Risk signals are accumulated atomically in Redis and translated into graduated responses — from allowing requests to light throttling, heavy throttling, or temporary bans.

The system also includes  **JWT authentication, RBAC, API-key management, PostgreSQL audit logging, Prometheus metrics, Docker Compose orchestration, and configurable security policies** .

What I focused on most was correctness under concurrent requests — using Redis atomic operations and Lua scripting to avoid race conditions while keeping the gateway lightweight and low-latency.

**Core technologies:** Python, FastAPI, Redis, Lua, PostgreSQL, SQLAlchemy, JWT, Prometheus, Docker.

2. VisionSphere — Enterprise Biometric Device Management & Synchronization System

The most complex Python system I have developed professionally is  **VisionSphere** , a proprietary desktop application for managing and synchronizing network-connected biometric and attendance devices across distributed locations.

I  **designed and developed the application independently from the ground up** , working across the device-integration, database, synchronization, concurrency, data-processing, and desktop UI layers. The system grew to **6,000+ lines of Python code** and integrates physical biometric devices, enterprise databases, external device APIs, and background processing into a single operational platform.

### What I Built

VisionSphere is built with  **Python and PyQt5** , backed by MySQL, and communicates directly with biometric/access-control devices through  **Hikvision ISAPI and HTTP Digest Authentication** .

The application handles:

* Device discovery, registration, configuration, and CRUD operations
* Retrieval and management of device metadata such as serial numbers, firmware, models, MAC addresses, and network configuration
* Real-time device health and connectivity monitoring
* Employee enrollment management across multiple devices
* Multi-device employee synchronization
* Attendance and punch-event retrieval and processing
* Employee search across online devices
* Excel/CSV-based configuration import and data export
* Background processing with progress reporting
* Structured logging and error handling
* Database-backed storage and encrypted device credentials

### Multi-Device Synchronization

One of the core components I developed was an automated  **multi-device enrollment synchronization pipeline** .

The workflow takes device configuration from Excel, validates source and destination relationships, checks device availability, retrieves employee enrollment information, and synchronizes the required user data across destination devices.

Rather than processing devices sequentially, I implemented **concurrent execution** so independent device operations could run in parallel. This was particularly important because communication with physical devices is network-bound and individual devices can become slow or unavailable.

The synchronization workflow therefore had to account for:

```
Configuration
      ↓
Validation
      ↓
Device Availability Check
      ↓
Source Enrollment Retrieval
      ↓
Concurrent Processing
      ↓
Destination Synchronization
      ↓
Progress / Error Reporting
```

### Concurrency & Background Processing

A significant engineering challenge was keeping the PyQt5 interface responsive while performing potentially slow network and database operations.

I used Python's concurrency primitives, including:

* `<span>threading.Thread</span>`
* `<span>ThreadPoolExecutor</span>`
* `<span>Queue</span>`
* Asynchronous network operations

For real-time punch updates, I implemented a **producer-consumer pattern** where background workers place updates into a queue and the Qt application receives them through signals, allowing network/device processing to remain separate from UI updates.

This required careful handling of shared state, background workers, timeouts, device failures, and communication with the main GUI thread.

### Device API Integration

The application communicates directly with biometric/access-control devices through their APIs rather than relying solely on database access.

I implemented integrations for operations including:

* Device information retrieval
* Employee/user search
* Employee creation and modification
* Card management
* Attendance/access-event retrieval
* User and card counts
* Face-library operations
* Remote device operations

The integration also involved  **HTTP Digest Authentication, JSON/XML response handling, pagination, network timeouts, and device-specific API behaviour** .

For example, large employee lists were retrieved using paginated API requests rather than assuming that the entire dataset could be returned in a single request.

### Database Architecture

The application integrates with multiple MySQL databases supporting different operational responsibilities, including device configuration, attendance/punch data, and employee information.

I developed the database layer responsible for:

* Connection management
* Parameterized database operations
* Device configuration persistence
* Attendance data retrieval
* Cross-database data retrieval
* Device credential storage and encryption

The application can combine device and attendance information to provide a unified operational view containing information such as the employee, punch timestamp, device, device location, and network identity.

### Attendance Processing

I also developed the attendance-processing workflow that transforms raw device events into meaningful attendance records.

The processing pipeline includes:

1. Fetching events from multiple devices
2. Normalizing timestamps
3. Sorting events by employee and time
4. Removing duplicate punches
5. Grouping events by employee and date
6. Pairing entry and exit events
7. Calculating attendance duration
8. Detecting incomplete entry/exit records
9. Generating detailed and summarized Excel reports

The system handles real-world cases such as missing exits, missing entries, duplicate punches, and incomplete attendance sequences.

### Why This Was Technically Challenging

What made VisionSphere significantly more complex than a typical Python CRUD application was the combination of  **software, networking, databases, and physical hardware** .

The overall system had to coordinate:

```
                 Python / PyQt5
                       │
                       ▼
              Background Processing
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
      Device APIs            MySQL
             │                   │
             ▼                   ▼
     Biometric Devices     Attendance Data
             │                   │
             └─────────┬─────────┘
                       ▼
              Data Processing
                       │
                       ▼
             Monitoring / Reporting
```

This meant dealing with problems that don't normally appear in isolated applications: network latency, offline devices, concurrent operations, API pagination, inconsistent device responses, database state, UI responsiveness, synchronization failures, and real-world hardware behaviour.

### Technology Stack

**Languages & Frameworks:**
Python, PyQt5

**Database:**
MySQL

**Device/API Integration:**
Hikvision ISAPI, HTTP/REST, HTTP Digest Authentication, JSON, XML

**Concurrency:**
Python threading, `<span>ThreadPoolExecutor</span>`, `<span>Queue</span>`, asynchronous network operations

**Data Processing:**
Pandas, OpenPyXL, Excel/CSV

**Other:**
Logging, network monitoring, credential encryption

### Confidentiality

Because VisionSphere was developed as part of my professional work,  **the original source code cannot be made public** . The codebase contains proprietary company logic, internal infrastructure information, device configurations, and other confidential implementation details.

I can, however, discuss the architecture, engineering decisions, synchronization strategy, concurrency model, database design, API integration, and the technical problems I solved during development. I can also provide a  **sanitized implementation demonstrating the underlying engineering concepts without exposing company intellectual property** . The proprietary nature of VisionSphere means the public repository cannot represent the complete original system, but I am comfortable walking through the implementation and technical decisions in an interview.

**This project gave me hands-on experience building a production-oriented system from the ground up, integrating software with physical devices, designing concurrent workflows, working with enterprise databases, and handling the failure modes that come with real-world infrastructure.**
