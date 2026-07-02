================================================================================
INTERVIEW MASTER STORY: NyAi COMPLIANCE SYSTEM
================================================================================
ROLE: Senior Backend/Distributed Systems Engineer
CONTEXT: Explaining the project to a Principal Architect during a 5+ YOE Interview.
================================================================================

"Hi, I'm glad to walk you through the NyAi Compliance System, which was one of the most architecturally challenging and rewarding platforms I've worked on. It's a B2B SaaS platform that automates regulatory compliance for Indian enterprises. I'll break down the business problem, our architectural decisions, the data flows, and the scaling challenges we tackled."

--------------------------------------------------------------------------------
1. THE BUSINESS PROBLEM & 2. WHY THE PRODUCT EXISTS
--------------------------------------------------------------------------------
In India, corporate compliance is incredibly complex. A mid-sized company might be subject to hundreds of acts, rules, and regulations (like the PF Act, Companies Act, GST, etc.), each with its own recurring filing deadlines. Missing a deadline can result in heavy financial penalties, revoked licenses, or even criminal liability for directors. 

Historically, companies managed this via massive Excel sheets and manual calendar reminders, requiring expensive legal consultants to interpret the law. NyAi exists to solve this by providing a centralized, automated source of truth. We built an "MDM" (Master Data Management) system curated by Subject Matter Experts (SMEs), which pushes legal obligations down to individual corporate tenants, automatically generating recurring tasks and using AI to match uploaded evidence to those tasks. 

--------------------------------------------------------------------------------
3. END-TO-END USER JOURNEY
--------------------------------------------------------------------------------
1. **Onboarding**: A company (Tenant) signs up and fills out an intelligent questionnaire regarding their industry, size, and operations.
2. **Discovery**: Our AI engine evaluates the profile and automatically assigns the relevant Acts to the company and distributes them to specific departments (e.g., HR gets Labor Laws, Finance gets Tax Laws).
3. **Task Generation**: The system translates the obligations of those Acts into a calendar of recurring tasks (monthly, quarterly, annually).
4. **Execution**: Department heads see their tasks on a dashboard, complete the physical compliance (e.g., paying PF), and upload the receipt (evidence).
5. **Verification**: The AI automatically reads the metadata of the uploaded receipt, ranks it against the task requirements, and auto-verifies the compliance. 

--------------------------------------------------------------------------------
4. END-TO-END SYSTEM FLOW (ARCHITECTURE)
--------------------------------------------------------------------------------
We architected the platform using Quarkus (for fast boot times and low memory in Kubernetes) and PostgreSQL, separating it into two distinct data boundaries to protect tenant isolation and ensure scalability:

**Boundary 1: The MDM Domain (`mdm_db`)**
- `mdm-core`: The central repository for all Acts, Rules, and Obligations, managed by SMEs.
- `mdm-subscriptions`: A replication broker that handles pushing/pulling data down to tenants.

**Boundary 2: The Compliance Domain (`compliance_dev`)**
- `compliance-core`: The main execution engine for the tenants (Task generation, departments).
- `compliance-auth`: Centralized IAM (Identity and Access Management) using Asymmetric JWTs.
- `compliance-ai`: The AI engine bridging compliance logic with LLMs (Claude).

We also have dedicated Liquibase migration services (`mdm-initial-data`, `compliance-initial-data`) to prevent schema deadlocks during deployments.

--------------------------------------------------------------------------------
5. HOW A TENANT IS ONBOARDED
--------------------------------------------------------------------------------
When a tenant registers, `compliance-auth` creates the user identity and issues an RSA-signed JWT. Simultaneously, a request is made to `mdm-core` to register the tenant in the global registry. `mdm-core` acts as an OAuth2 Authorization Server and generates a `client_id` and `client_secret` for this specific tenant, allowing their local `compliance-core` instance to securely pull data from the MDM ecosystem using the `client_credentials` grant type.

--------------------------------------------------------------------------------
6. HOW LEGAL OBLIGATIONS ENTER THE SYSTEM
--------------------------------------------------------------------------------
SMEs log into the `mdm-core` dashboard and input new laws or amend existing ones. We implemented an Aspect-Oriented Programming (AOP) interceptor (`@ChangeLogged`) on the service layer. Any time an SME creates, updates, or deletes a provision or obligation, the interceptor automatically writes the delta to a `change_logs` table with an incrementing sequence number. This is the foundation of our CDC (Change Data Capture) mechanism.

--------------------------------------------------------------------------------
12. HOW MDM SYNCHRONIZATION WORKS
--------------------------------------------------------------------------------
Tenants need this updated data, but letting 10,000 tenants poll the MDM database would cause a DDoS effect. 
We built an asynchronous, cursor-based chunked replication system in `mdm-subscriptions`:
- Each tenant has a `SubscriptionCursor` tracking their `lastAckedSequence`.
- A Quartz scheduler (`ChangeJobWorker`) runs every 5 minutes. It identifies tenants who are lagging behind the MDM `change_logs`.
- It bundles the missing changes into a `ChangeJob`, slicing the payload into `ChangeChunk`s (e.g., 20 records each) and calculates an MD5 checksum.
- `compliance-core` fetches these chunks, applies the SQL inserts/updates locally, verifies the checksum, and hits a `/consume` endpoint to advance their cursor. 

--------------------------------------------------------------------------------
7. HOW OBLIGATIONS BECOME COMPLIANCE TASKS
--------------------------------------------------------------------------------
Once the tenant's `compliance-core` database receives the new obligations, it must generate actionable tasks. Doing this synchronously on page-load would crash the DB. Instead, we heavily rely on Quartz Schedulers configured in Clustered Mode. Background workers read the frequency of the obligation (e.g., "File GST by the 15th of every month") and generate `TaskInstance` records for the upcoming cycle.

--------------------------------------------------------------------------------
8. HOW DEPARTMENTS RECEIVE TASKS
--------------------------------------------------------------------------------
Tasks belong to Acts, and Acts must be assigned to Departments. Our `compliance-ai` service runs an `AiAutoAssignScheduler`. It takes the tenant's profile, fetches the available Acts, and uses Claude (LLM) to intelligently map the Acts to the correct Departments based on the department's description. The task generation engine then assigns the newly created tasks to the Department Head.

--------------------------------------------------------------------------------
9. HOW EVIDENCE IS UPLOADED & 10. HOW AI IS INVOLVED
--------------------------------------------------------------------------------
When a user uploads a PDF receipt, it hits our `evidence-service` which performs OCR and extracts metadata (keywords, dates, document type, and a 2-line summary). 

We faced a massive challenge here: How do we use AI to verify if the document matches the task without spending thousands of dollars on LLM tokens or leaking PII? We evaluated Vector RAG (Retrieval-Augmented Generation) but discarded it—vector embeddings fail at compliance nuances (e.g., "PF Challan Jan" vs "PF Challan Feb" are too semantically similar). 

Instead, I designed the `ClaudeRankingService`. We send ONLY the extracted metadata (~300 characters) to Claude, along with the specific task requirements. Claude ranks the relevance (e.g., Score 0.95) and verifies the date logic. If the score passes a threshold, the `AiEvidenceAutoAssignScheduler` automatically links the evidence to the task and marks it complete.

--------------------------------------------------------------------------------
11. HOW NOTIFICATIONS WORK
--------------------------------------------------------------------------------
`compliance-core` runs daily Quartz jobs that query tasks approaching their due dates. It bundles these alerts and triggers asynchronous emails (via SMTP configs in the database) to the assigned users and escalates to managers if a task is overdue.

--------------------------------------------------------------------------------
13. SCALABILITY CHALLENGES
--------------------------------------------------------------------------------
1. **DB Lock Contention on Startup**: With multiple Quarkus nodes starting simultaneously, Hibernate auto-generation caused split-brain schemas. We disabled ORM generation globally and built the `compliance-initial-data` microservice to exclusively run Liquibase migrations using an init-container pattern.
2. **Clustered Schedulers**: If 5 instances of `compliance-core` ran the Daily Task Generator, we'd get 5x duplicate tasks. We configured Quartz with PostgreSQL-backed `QRTZ_LOCKS` tables. Nodes use pessimistic locking (`SELECT FOR UPDATE`) to acquire the trigger, ensuring exactly-once job execution.
3. **Out of Memory (OOM) on Initial Sync**: When a new tenant is onboarded, they need the entire database of laws. Sending 50MB of JSON caused OOMs. We built `SnapshotJobs` that slice the initial load into paginated chunks, allowing the tenant to process them reliably.

--------------------------------------------------------------------------------
14. PRODUCTION ISSUES THAT COULD OCCUR
--------------------------------------------------------------------------------
- **Token Expiry during Syncs**: Our Asymmetric JWTs expire in 15 minutes for security. If an MDM sync takes 20 minutes due to a massive government legal update, the chunks will start returning 401 Unauthorized mid-flight. The client must handle 401s gracefully, use the refresh token, and resume from the last unconsumed chunk.
- **LLM Rate Limiting**: If 100 tenants upload evidence simultaneously, Anthropic/Claude API rate limits could be breached. We mitigate this using a `Semaphore` in the AI schedulers to strictly cap concurrent tenant processing.

--------------------------------------------------------------------------------
15. WHAT IMPROVEMENTS I WOULD MAKE TODAY
--------------------------------------------------------------------------------
1. **Replace Application-level CDC with Debezium**: Currently, we rely on developers remembering to use the `@ChangeLogged` annotation to track MDM changes. If someone runs a raw SQL update, it bypasses the interceptor, breaking replication. I would rip this out and replace it with Debezium (Kafka Connect) reading directly from the Postgres Write-Ahead Log (WAL) to ensure 100% accurate CDC.
2. **Event-Driven Architecture**: The current MDM chunk pulling mechanism is essentially batch-polling every 5 minutes. Moving to an Event-Driven architecture with Kafka would allow real-time pushing of changes while retaining backpressure.

--------------------------------------------------------------------------------
16. MY ROLE ON THE PROJECT & 17. FEATURES I WORKED ON
--------------------------------------------------------------------------------
As a Senior Backend Engineer, my focus was on distributed systems reliability and platform scalability. I specifically designed and implemented:
- The **Cursor-Based Chunked Replication System** (`mdm-subscriptions`), solving the OOM and DDoS challenges of tenant data synchronization.
- The **Metadata-Only AI Ranking Engine** (`ClaudeRankingService`), reducing LLM costs by 99% and entirely eliminating PII data leaks to third-party AI models.
- The **Clustered Quartz Task Generation Engine**, implementing transactional boundaries and chunking to ensure massive recurring task creation didn't lock the database.
- The **Decentralized Authentication Architecture**, setting up the RSA-based asymmetric JWTs across all microservices so they could validate tokens statelessly.

================================================================================
18. 50 REALISTIC INTERVIEWER FOLLOW-UP QUESTIONS
================================================================================

### Architecture & System Design
1. Why did you choose Quarkus over Spring Boot for this architecture?
2. Explain the difference between your MDM domain and Compliance domain. Why not use a single database?
3. How did you decide on the microservice boundaries? Could compliance-ai have been a module in compliance-core?
4. Walk me through the cursor-based replication. What happens if a tenant's database crashes midway through consuming a chunk?
5. You mentioned Debezium as an improvement. How exactly does Debezium read from the WAL, and what infrastructure would you need to add?
6. If a tenant deletes their account, how does the system handle the cascading deletion across MDM and Compliance databases?
7. How does the system handle schema changes across the isolated tenant databases?
8. Why did you isolate Liquibase into `compliance-initial-data` instead of using Kubernetes init-containers running Flyway directly?
9. What happens if the MDM database goes down? Does the tenant application crash?
10. How do you handle multi-tenancy? Is it row-level (tenant_id) or schema-per-tenant?

### Database & Scalability
11. Explain how Quartz clustered mode achieves locking in PostgreSQL.
12. If a Quartz job fails halfway through generating tasks for a tenant, how do you prevent duplicate generation on the next run?
13. You mentioned `@Transactional(REQUIRES_NEW)`. How does connection pooling handle this if you nest transactions?
14. How do you handle pagination in your REST APIs when dealing with millions of tasks?
15. What indexes would you put on the `change_logs` table to ensure fast querying by `mdm-subscriptions`?
16. Explain your strategy for handling Out Of Memory (OOM) errors during the Snapshot Sync.
17. How do you scale the WebSocket or polling mechanisms if 10,000 tenants are checking for jobs every 5 minutes?
18. If the `change_logs` table grows infinitely, how do you archive or purge old logs without breaking tenants who have been offline for months?
19. What isolation level does your database run at, and did you face any phantom read issues during task generation?
20. How do you ensure idempotent API calls, especially for the `/consume` chunk endpoint?

### AI & Integrations
21. Why exactly does Vector Similarity (RAG) fail for compliance tasks?
22. Walk me through the exact JSON prompt you send to Claude for document ranking.
23. How do you handle Claude API timeouts or 503 errors during evidence ranking?
24. You mentioned a Semaphore for rate limiting. Does that work across a distributed cluster, or is it JVM-local?
25. How would you implement a distributed rate limiter if you have 10 instances of `compliance-ai`?
26. If the AI incorrectly maps an Act to the wrong Department, how does the user correct it, and does the AI learn from this feedback?
27. How does the Gap Analysis service handle batching? What if a batch exceeds the token limit?
28. Explain how you process the intelligent questionnaire into an Entity Profile.
29. How do you ensure that the AI doesn't hallucinate a non-existent legal obligation?
30. If you swap Claude for OpenAI tomorrow, how decoupled is your AI client code?

### Authentication & Security
31. Explain Asymmetric JWT validation. How does `compliance-core` get the public key?
32. What happens if the RSA Private Key is compromised? How do you rotate keys in this architecture?
33. Why use HttpOnly cookies instead of storing the JWT in LocalStorage?
34. How does the system defend against CSRF attacks since you are using cookies?
35. How is the MDM OAuth2 `client_credentials` flow secured? Where is the secret stored?
36. If a tenant's access token expires mid-sync, you mentioned using the refresh token. Walk me through that HTTP flow.
37. How do you handle authorization (RBAC) inside `compliance-core`? Does the JWT contain roles?
38. What is the authorization middleware doing in `mdm-core`?
39. How do you securely store the SMTP passwords and database credentials?
40. Have you implemented rate limiting on the `/token` endpoint to prevent brute forcing?

### Production & DevOps
41. How do you trace a user's request across `compliance-core`, `compliance-ai`, and `evidence-service`?
42. What metrics are you exporting from Quarkus (e.g., Micrometer/Prometheus) to monitor the Quartz schedulers?
43. How do you handle graceful shutdown of a node that is currently processing a 20-chunk MDM change job?
44. If a bug in `compliance-initial-data` corrupts the Liquibase `DATABASECHANGELOG` table, how do you recover?
45. Explain how you test the `@ChangeLogged` AOP interceptors.
46. What happens if the `evidence-service` OCR engine takes 10 minutes to process a 500-page PDF? Does it block the HTTP thread?
47. How do you structure your logs so that you can easily debug a failure in the LLM ranking?
48. What alerting thresholds would you set for the MDM sync delay (Lag)?
49. How do you handle database migrations that require data transformation, not just schema changes?
50. Looking back, what was the most difficult bug you resolved in this system?

================================================================================
END OF INTERVIEW MASTER STORY
================================================================================
