# Healthcare

## Healthcare Data Standards & Compliance


Healthcare systems are built by different companies for ex :
	Hospital software , 
	Pharmacy software, 
	Lab Software, 
	Insurance software etc

- But the problem is Each system may use different technologies. But all of these software must exchange patient data safely & effectively. Poor data exchange can impact patient care.

- So to solve these problem healthcare uses these below data standard formats to communicate with each other. 

1. **HL7 (Health Level Seven)**
2. **FHIR (Fast Healthcare Interoperability Resources, pronounced "Fire")**

>[!note]

As a full-stack developer, you will be handling data. In healthcare, you don't get to invent your own JSON structures for patient records; you must follow industry standards.
### The Data Standards: HL7 vs. FHIR
### 1. HL7 (Specifically v2)

HL7 v2 is one of the most widely used legacy healthcare messaging standards. It is message-based and uses pipe-delimited strings (e.g., PID|1||123456^^^…). Things to know about HL7 :

- Mostly used in legacy systems
- HL7 is message-based
- Pipe-separated format

- Understand This Structure below : HL Example :  

- MSH|^~\&|HIS|Hospital|LIS|Lab|202504021200||ORM^O01|12345|P|2.3 
- PID|1||123456^^^Hospital||Doe^John||19800101|M|||Delhi 
- OBR|1||54321|CBC^Complete Blood Count 
- OBX|1|NM|WBC^White Blood Cells||5.5|10^9/L|4.0-11.0|N

Explanation:

- MSH →Message Header
- PID → Patient Information
- OBR → Order Request 
- OBX → Observation/Result 
- This message sends lab test request & result. 

### 2. FHIR

FHIR is a modern healthcare standard. Instead of dense, pipe-delimited text messages, FHIR commonly uses RESTful APIs over HTTP and supports JSON/XML formats **for exchanging healthcare data between systems**. 

**Developer Context :** 
If you want to get a patient's data in FHIR, your frontend makes a standard HTTP request like GET /fhir/Patient/123, and the backend returns a clean JSON object.

  
```json
{
	"resourceType": "Patient",
	"id": "123",
	"name": [
		{
		"family": "Doe"
		}
	]
}
```

SMART on FHIR is an industry standard that combines **FHIR** (for data) with **OAuth2 and OpenID Connect** (for security). If an interviewer asks how a third-party app securely connects to an Electronic Health Record (EHR) system, "SMART on FHIR" is the exact keyword they want to hear.

**Testing FHIR** 
Mention that developers use public sandbox servers like **HAPI FHIR** or **Logica Sandbox** to test REST API calls without touching real patient data.

---
## Interoperability

Interoperability means different healthcare systems can exchange, understand, and use medical data correctly.

Example: A hospital system should be able to send patient lab reports to a pharmacy or insurance system without data loss or format issues.

HL7 and FHIR are designed to improve interoperability between healthcare systems.

---

## The Middleware: Integration Engines (Mirth Connect)

Healthcare systems often use different formats and standards. If some legacy system is using HL7 and some modern system is using FHIR, how do they talk to each other?

There can be a full of mismatch between systems.

Mirth Connect (now known as NextGen Connect) is an open-source healthcare integration engine used to exchange data between different healthcare systems.

It converts data from one format to another format  

It takes a modern FHIR JSON request from your app, translates it into an old-school HL7 pipe-delimited message, sends it to the legacy system, and translates the response back.

Interview Prep: Understand the concept of "Middleware." Be prepared to sketch or explain a system design where your full-stack app does not connect directly to the hospital's core database, but rather communicates through an integration engine or an API gateway.

Frontend App → FHIR API → Backend Services → Integration Engine (Mirth Connect) → HL7 → Hospital/Lab Systems

---
## Compliance & Security: 

In e-commerce, a leaked password is bad. But in healthcare, a leaked medical record is a federal offence that can cost millions in fines.

### HIPAA (Health Insurance Portability and Accountability Act) 
HIPPA is a US healthcare law for protecting patient data. Healthcare companies need to follow this. You must understand the HIPAA Rules and technical safeguards of the HIPAA Security Rule.

### PHI (Protected Health Information): 
This is any data that links an individual's identity to their health condition (Patient Name + Diagnosis, Patient Phone Number + Medical Record). 

**PHI Protection Techniques :**

- **Backend :** Encryption at rest and audit logging (tracking activities like exactly who queried a patient record and when).

- **Transit (Network):** Everything must be over HTTPS/TLS.

- **Access (Full-Stack):** Implementing strict Role-Based Access Control (RBAC) using OAuth2 or JWTs. A nurse shouldn't see what an admin sees.

- **UI/Frontend:** Data masking (e.g., showing only the last 4 digits of a Social Security Number on the screen, **Example:** Mask SSN → XXX-XX-1234​).

---
### What is a BAA (Business Associate Agreement)

- BAA is a legal contract between: A healthcare organization (like a hospital) And a third-party vendor (like a software company, cloud provider like AWS, etc.) 

- When a vendor handles or accesses PHI (patient data), they must: Follow HIPAA rules , Keep data secure, Not misuse patient information.

- If your company uses AWS to host the database, AWS must sign a BAA legally promising they will handle that PHI according to HIPAA rules. 

- Security Architecture (Putting it Together) The presentation ends by tying everything back to safe communication. 

**Developer Context:** 

When designing a full-stack system, you can't just use basic session cookies. You should talk about implementing **OAuth2** for authentication (proving who the user is) and strict **Role-Based Access Control (RBAC)** for authorization (proving what the user is allowed to see). For example, a doctor logging in with an OAuth2 token should have authorization to see clinical data, while a billing admin with a different token should only see financial data.

---