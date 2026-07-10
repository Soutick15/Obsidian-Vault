

# Form Builder Module 

It is a module of our Healthcare project.

# Self Introduction :

Hi, good afternoon. My name is Soutick.

I am a Java backend developer with a 5+ years of experience.

I have Mostly worked in the healthcare and supply chain management domains, where I have focused on building scalable and reliable backend systems.

From a technical perspective, I have a strong foundation in Java and its frameworks such as Spring, Spring Boot, Hibernate, where I have worked on both Rest APIs a and GraphQL. 

On the database side, I’ve worked on Both relational and non-relational databases like MongoDB and MySQL

For service-to-service communication, I’ve mainly used Kafka. 

For testing purposes  I used JUnit and Mockito to ensure robust and maintainable code.

I have hands-on experience with AWS and GCP services.

---

## Form builderArchitecture


![[Pasted image 20260710230429.png]]

---

## Project Introduction : 

-  I have worked on a Health care portal and in this project I worked in Form Builder module. 
- The portal is used by US state governments to manage and onboard healthcare providers such as Doctors, Hospitals, Pharmacist, and Health Insurance companies. 
- Provider register their details like ( specialty, service location, license Affiliation etc) when the submit —> Then their application go through an approval process, and become active providers on the platform . 
- Here the Providers register by filling out huge complicated forms for submitting licenses, credentials, etc so they can give the service to the needy people.
- Through the platform common people can find the best and required service available according to their need.

### Why form Builder?

- These forms are big, it is having like hundreds of fields. So, we are using a Form Builder tool from which we can dynamically create and configure form for different enrollments.  
- We want to ask some question, or need some data to fill in the form, so if I want to add new question I need developer to hardcode the values.
- So, using this form builder tool we can create new form field dynamically.
- These **forms render automatically** based on the configuration we provide in the form builder tool and using **JSON templates** sent by backend APIs. (sections, groups and fields) and rendered at runtime as provider applications.

  
### How does you healthcare application work? 

The lifecycle of a Provider in "Healthcare app" consists of:   
    1. User Registration   
    2. Form Submission   
    3. Approval Process   
    4. Becoming an Active Provider   
    5. Termination (if required) 

  

#### Form Rendering and Section APIs, Internal working of the form builder: 

"Healthcare app" uses a dynamic form builder approach with forms created from JSON definitions to generate the form: 

- **Application Collection:** Contains Sections > Groups> Fields hierarchy . This is used for template. It contains all the form questions, the options, Layouts, rules etc.
- **RuntimeApplication Collection :** Contains RuntimeSections > RuntimeFields(groups) > RuntimeFields(fields) hierarchy. It is used to store the answers and other metadata of the form.
- The **form structure** follows a hierarchy:

- Section → contains multiple Groups
- Group → contains multiple Fields
- Field → actual form questions like drop-downs, inputs, etc.

  

  

**Section -** fieldType = SECTION

**Group -**  fieldType = TOPIC

**Field -** fieldType = “CHOICE”, “TEXT”, “EMAIL” etc

**Custom Section -** “fieldType": “CUSTOM_SECTION_NAME”,…},.. ] (Hardcoded Values)

  

**Mapping in Frontend** 

Application == RuntimeApplication   
Section (ID) == RuntimeSection (ID)   
Field (ID) == RuntimeField (ID) 

---  
#### User Roles: Internal & External

##### Internal Users:
Admin/ Government officials who manage form configurations and have the authority to verify, approve or deny enrollments based on the information provided in the forms. Internal user has access to all configurations and system options. Holds authorization to change system settings.

##### External Users: 

Providers who are filling the forms like doctors and organizations that seek to enroll. We have different Types of Enrollments for different types of providers:

1. **Individual Enrolment:** For solo practitioners, like a single doctor or nurse. One person handling all the environment.
2. **Entity Enrolment:** For a group of people or hospital.
3. **Trading Partner Enrolment:** For medical facilities.
4. **Managed Care Organization (MCO) / Auto Provider Enrollment :** Manages services and operations at the hospital level.
5. **Provider Enrolment Manager (PEM) :** Oversees the entire environment, acts as the manager of enrollments and operations. Manages multiple enrollments.


---

#### Roles an Responsibility - Features I build :

##### Datasource:
A centralised list of dropdown options provider. we need datasource for the dropdown. Suppose we have a field that requires more than 100 options to populate the drop-down list. It’s challenging to give all those options by the admin, so we’ll create a data source and generate the file based on the user’s request. To avoid hardcoding options again and again inside forms. 

And from next time onwards, whenever we call the API, we will fetch the data from the Mango DB.

  

---
>[!question] Interviewer: Can you tell me the challenges you faced?

- Yes. Recently I worked on a feature called “referFrom” in our dynamic form builder.
- This feature allows admins to configure dropdown fields so that their options are pulled dynamically from previously submitted form data. For example, an admin can select which earlier fields should appear as selectable options in another dropdown. This configuration is stored in a property called referFromTableOptions.
- The biggest challenge was performance. The referFrom API was taking close to a minute, which was completely unacceptable for production.
- After analyzing the root issue, I found several problems:
- Each API call was fetching the full Application template from MongoDB. These templates are very large and deeply nested.
- The system searched fields recursively through sections → fields → nested fields every time. This was happening with no optimization or indexing.
- No caching : Even if the same template or field was requested repeatedly, it always hit the database.
- MongoDB aggregations was Unoptimised cause We support multiple field types (normal fields, table fields, multi-entry fields), but the aggregation queries were not optimized for each case.

 **Can you tell me how you resolved it:**


---

>[!question] If some answers you dont know

I haven’t used this technology directly, but I know it’s used for event streaming and decoupling microservices.

---


  

**taxonomyInfo collection** : Here we can find all the relationship between Taxonomy, ProviderType etc based on golden configuration sheet.

  

For different Enrollments we have different taxonomy. PEM no taxonomy.

**2. Taxonomy , Specialty, ProviderType :** In medical terminology, taxonomy and specialty refer to different layers of classification for healthcare providers, and they’re often used together in healthcare portals, provider directories, and claim systems.

  

- **Taxonomy:** A standardized code (1223G0001X) that classifies both the provider type and specialization. It’s used in claims, credentialing, etc.
- Used to uniquely identify a provider’s role and scope in billing systems. 207Q00000X = “Family Medicine Physician”
- **Specialty :** A more general term that describes what field a provider practices in (non-coded). For example-  “Cardiology”, “Pediatrics”, “Neurology”
- Used for display, filtering, or user selection on portals/forms.
- **Provider Type :** **Dental Provider**

  

**Now How The Normal Section is Getting stored:** 

  

After filling or updating one answer in the normal section, the data is immediately stored in the runtimeSection through web sockets. “AnswerChangedEvent” is called 

[ Request url: wss://dyp-sbqa-01.dyp.cloud/api/hummingbird/runtimeAppEvents/c7cd4973-70ba-4311-a3ad-a7617bef7b20the 

  

Response 

AnswerChangedEvent(answer=Answer(value=121-21-2122, answerStatus=null, permissionValues=null, timestamp=1750328246533), previousAnswer=Answer(value=121-21-2122, answerStatus=null, permissionValues=null, timestamp=1750328246299), runtimeFieldId=cbb4008f-3816-4aa1-a43a-3556166e8004)"

]

  

- **Program Participation:** The healthcare programs or insurance plans the provider is enrolled in. Like Medicare, Medicaid, Blue Cross
- **Service Location :** Physical places where the provider offers services. Example one doctor has clinic in NYC, Hospital in Bangalore where he provide his service. There are primary and secondary service locations. The service location is dependent on the taxonomy, meaning the speciality of the provider determines the service location details.
- **Affiliation Section :** Affiliation allows users to affiliate with other users or enrollments. It tells which hospitals or organizations is the provider is connected to or linked with, like hospitals, groups, or healthcare organizations. Suppose a Doctor is affiliated with Apollo Hospital, or a NY Physicians Group.


________________________________________________________________________________________

 - **Some API used in the form builder:**
- **To validate an user with the email address:** 

PATCH - [https://dyp-sbqa-01.dyp.cloud/api/providermgmt/authenticate/eventCapture/validate/soutik@sharklasers.com](https://dyp-sbqa-01.dyp.cloud/api/providermgmt/authenticate/eventCapture/validate/soutik@sharklasers.com)

PATCH - [https://dyp-sbqa-01.dyp.cloud/api/providermgmt/authenticate/eventCapture/validate/internal.user.dyp+cd@gmail.com](https://dyp-sbqa-01.dyp.cloud/api/providermgmt/authenticate/eventCapture/validate/internal.user.dyp+cd@gmail.com)

  

  

**To fetching service location names to populate a dropdown menu.**

GET - [https://dyp-sbqa-01.dyp.cloud/api/hummingbird/ssl/getServiceLocationNamesForDropdown/e9bfd956-66de-43a4-85f8-ddcbe16d97d0/false](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/ssl/getServiceLocationNamesForDropdown/e9bfd956-66de-43a4-85f8-ddcbe16d97d0/false)

  

**This API is used in the UI (likely in an AG Grid or similar table) to display a list of service locations for a provider or application, with support for filtering, sorting, and pagination :**

GET - [https://dyp-sbqa-01.dyp.cloud/api/hummingbird/ssl/search?runtimeAppId=e9bfd956-66de-43a4-85f8-ddcbe16d97d0&direction=desc&page=0&size=10&sortBy=sslSeqId&address=&city=&state=&zipCode=&locationType=&locationName=&isProviderId=false&requestType=PEM&endedSl=false](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/ssl/search?runtimeAppId=e9bfd956-66de-43a4-85f8-ddcbe16d97d0&direction=desc&page=0&size=10&sortBy=sslSeqId&address=&city=&state=&zipCode=&locationType=&locationName=&isProviderId=false&requestType=PEM&endedSl=false)

**When Uploading a Document like pdf for license type on any section :** 

POST -  [https://dyp-sbqa-01.dyp.cloud/api/hummingbird/integration/upload](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/integration/upload)

POST - [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/integration/upload](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/integration/upload)

  

  

This is also getting called : [https://dyp-sbqa-01.dyp.cloud/api/hummingbird/auditEventsChange](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/auditEventsChange)

  

  

  

_____________________________________________________________________________________________________________________________________________


  

**This web socket is getting called when filled the form fields :**

 wss://fl-dyp-sb.hhstechgroup.com/api/hummingbird/runtimeAppEvents/55c869de-a332-44bf-b2c1-78d5be084d83

  

**WebSocket Handler Layer Class:** RuntimeEventsHandler.java

This class receives the WebSocket message and deserializes it into an AnswerChangedEvent (a subclass of BaseWSEvent).

  

**Event Model**  **Class:** AnswerChangedEvent.java

This class represents the event payload. It has an apply(EventApplier) method.

  

  

|                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Ping:{"type":"answerChangedEvent","id":"36ca760f-1654-4638-8d70-c842feb8240b","timestamp":1751008385147,"answer":{"value":"To ONLY participate in the network of a Medicaid health plan. *","type":"simple","timestamp":1751008385147,"typeStatus":"DEFAULT"},"previousAnswer":{"value":"To ONLY participate in the network of a Medicaid health plan. *","type":"simple","timestamp":1751008385147,"typeStatus":"DEFAULT"},"runtimeFieldId":"1e05f98a-139f-4038-8b94-bd7e297e75ca"} |
| pong : ”gAnswerChangedEvent(answer=Answer(value=To ONLY participate in the network of a Medicaid health plan. *, answerStatus=null, permissionValues=null, timestamp=1751008385568), previousAnswer=Answer(value=To ONLY participate in the network of a Medicaid health plan. *, answerStatus=null, permissionValues=null, timestamp=1751008385147), runtimeFieldId=1e05f98a-139f-4038-8b94-bd7e297e75ca)"                                                                          |

  

________________________________________________________________________________________


**After saving one Taxonomy Entry, this add a new Taxonomy (TX) detail to a Service Location.**

POST - [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/addTX/false](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/addTX/false)

  

**This API endpoint is designed to get the names of all Program Participations (PPs) or Taxonomies that are associated with a specific runtime application. It effectively returns a list of all available specialties for a given application context.**

GET - [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getPPNames/55c869de-a332-44bf-b2c1-78d5be084d83/0/false](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getPPNames/55c869de-a332-44bf-b2c1-78d5be084d83/0/false)

  

  

**This API is fetching a paginated and sorted list of Program Participations (PPs) associated with a specific service location or application. In your system, "Program Participation" is often used interchangeably with "Taxonomy" or "Provider Specialty" (e.g., Cardiology, Pediatrics, etc.).**

  

GET [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getPPs/55c869de-a332-44bf-b2c1-78d5be084d83?direction=asc&page=0&size=10&sortBy=effectiveEndDate&isProviderId=false](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getPPs/55c869de-a332-44bf-b2c1-78d5be084d83?direction=asc&page=0&size=10&sortBy=effectiveEndDate&isProviderId=false)

  

  

  

**Service Location Custom sections:**

  

**Inside service location section -> Location Specialty/Taxonomy||Add Specialty/Taxonomy, we are fetching the provider type :** 

This API endpoint is designed to **get a list of all Program Participations (Taxonomies) for a given service location, filtered by a specific specialty**. This is used to find all taxonomies that fall under a broader specialty category for a particular service location.

GET - [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getProgramParticipations/0?runtimeId=55c869de-a332-44bf-b2c1-78d5be084d83&specialty=SURGERY,%20GENERAL%20-%20055](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getProgramParticipations/0?runtimeId=55c869de-a332-44bf-b2c1-78d5be084d83&specialty=SURGERY,%20GENERAL%20-%20055)

  

  

**Then saving the Location Specialty/Taxonomy||Add Specialty/Taxonomy section we are calling this :** 

This API fetches a **paginated and sorted list of Program Participations (PPs) that are associated with a specific Service Location (SL)**. It also retrieves a set of dynamic questions related to these taxonomies.

GET - [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getPpsInSl/55c869de-a332-44bf-b2c1-78d5be084d83/individual/0?direction=asc&page=0&size=10&sortBy=locationTaxonomyEffectiveEndDate&isProviderId=false](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/getPpsInSl/55c869de-a332-44bf-b2c1-78d5be084d83/individual/0?direction=asc&page=0&size=10&sortBy=locationTaxonomyEffectiveEndDate&isProviderId=false)

  

  

**This API is used to update the list of Program Participations (PPs) associated with a specific Service Location (SL). In your system, "Program Participation" is often used to represent a provider's specialty or taxonomy (e.g., Cardiology, Pediatrics, etc.).**

  

**After adding one Add Specialty/Taxonomy:** 

PATCH - [https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/updatePPToSl/55c869de-a332-44bf-b2c1-78d5be084d83/0/false/false](https://fl-dyp-sb.hhstechgroup.com/api/hummingbird/serviceLocation/updatePPToSl/55c869de-a332-44bf-b2c1-78d5be084d83/0/false/false)

  

serviceLocationTaxonomyDetails

approvedServiceLocationTaxonomyDetails

  

  

**Data Source APIs**

  

**Fetching Taxonomy bases on: enrollment type + Practice Type + application type** 

[https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/taxonomy/?applicationType=To%20ONLY%20participate%20in%20the%20network%20of%20a%20Medicaid%20health%20plan.%20%2A&enrollmentType=individual&practiceType=SOLE%20PROPRIETOR](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/taxonomy/?applicationType=To%20ONLY%20participate%20in%20the%20network%20of%20a%20Medicaid%20health%20plan.%20%2A&enrollmentType=individual&practiceType=SOLE%20PROPRIETOR)

  

  

**Fetching Specialty  bases on : enrolment type + taxonomy name.**

[https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/specialty/?enrollmentType=individual&taxonomyName=208600000X](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/specialty/?enrollmentType=individual&taxonomyName=208600000X)

  

  

**Fetching Provider-type based on : Enrolment type + specialty + taxonomy name:** 

[https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/provider-type/?enrollmentType=individual&specialty=SURGERY%2C%20ABDOMINAL%20-%20052&taxonomyName=208600000X](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/provider-type/?enrollmentType=individual&specialty=SURGERY%2C%20ABDOMINAL%20-%20052&taxonomyName=208600000X)

  

  

**Fetching License-type based on : enrolment type + providerType + specialty + TaxonomyName** 

[https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/license-type/?enrollmentType=individual&providerType=PHYSICIAN%20%28D.O.%29%20-%2026&specialty=SURGERY%2C%20ABDOMINAL%20-%20052&taxonomyName=208600000X](https://dyp-sbqa-01.dyp.cloud/api/hummingbird/dataSource/details/license-type/?enrollmentType=individual&providerType=PHYSICIAN%20%28D.O.%29%20-%2026&specialty=SURGERY%2C%20ABDOMINAL%20-%20052&taxonomyName=208600000X)

  

- We use Kafka for event-driven communication between microservices, specifically for:

- **Provider Status Updates**: When providers are approved/rejected, we publish events to Kafka
- **License Processing**: Data Integration Service consumes license update requests in batches
- **Dead Letter Queues**: Failed messages are sent to DLQ with retry mechanisms
- **Real-time Notifications**: WebSocket events are published through Kafka for real-time updates
- Key features implemented:
- Batch processing (500 messages per batch)
- Exponential backoff retry (3 retries, 3-15 second intervals)
- Dead Letter Queue for failed message handlingConcurrent processing (2 consumer threads)
- Conditional enablement (can be disabled via configuration)
- This architecture ensures reliable, scalable, and real-time communication between our healthcare provider management services."

  

  

  

  

**Project Name:** DAI Project (Supply Chain & Bidding Platform for East Africa – Uganda, Tanzania, etc.)

**Domain:** Supply Chain Management / B2B Marketplace

  

**1. Project Overview**  
The DAI Project is essentially a **digital marketplace platform** designed for regions like **Uganda, Tanzania, and similar African countries**.

- The platform works as a **B2B supply chain system** where:

- **Suppliers** can showcase their products (e.g., agricultural goods, crude oil, raw materials, etc.).
- **Buyers** can browse these products and place **quotations (bids)**.
- If the buyer’s offer matches or is accepted by the supplier, the purchase can be completed.

In simple words – it’s like a **procurement and bidding portal** tailored for country-specific markets.

  

**2. Key Features**

- **Country-specific UI/branding:**  
    Depending on the region (Uganda, Tanzania, etc.), the platform customizes the UI and relevant details.
- **Supplier Module:**  
    Suppliers can:

- Register on the platform (after admin approval).
- Upload their goods, images, and descriptions.
- Set pricing and availability.

- **Buyer Module:**  
    Buyers can:

- Browse goods.
- Place bids/quotations.
- Negotiate and finalize deals with suppliers.

- **Admin Portal:**  
    Admin manages:

- Buyer & Supplier approvals.
- Platform access & subscription fees.
- Monitoring of transactions and quotations.

- **Payment & Notification Services:**

- Integrated **payment gateway** for transactions.
- **Notification service** (emails, alerts) for bids, approvals, and order updates.

  

**3. Technical Architecture**

- **Backend:** Java (Spring Boot based microservices)
- **Services:**

- **Management Service** – handles core business logic.
- **Notification Service** – for email/SMS updates.
- **Payment Service** – for handling platform charges and supplier-buyer transactions.
- **Catalog Service** – for supplier product listings.

- **Database:** MongoDB (storing suppliers, buyers, goods, bids, transactions).
- **DevOps/Infra:**

- Multiple environments: **Dev** **→** **Stage** **→** **Demo** **→** **Prod** **→** **Post-Prod**.
- **Post-Prod Environment:** Replica of production with daily DB backups, used for testing without impacting live users.

  

**4. Deployment Pipeline**

- **Dev:** Developer testing.
- **Stage:** QA verification.
- **Demo:** Client demo environment for validation.
- **Prod:** Live production for real users.
- **Post-Prod:** Mirror of production for testing new features & bug fixes safely.

  

**5. Example Workflow**

1. Supplier registers → pays subscription fee → gets admin approval.
2. Supplier uploads product details (e.g., 100 gallons of crude oil).
3. Buyer visits platform → searches goods → places a bid (say $100 per gallon).
4. Supplier checks bid → if accepted → transaction proceeds via payment gateway.
5. Both parties get notified via email/SMS.
6. Admin monitors transactions and platform health.

  

**6. Why is this project impactful?**

- It’s solving a **real problem** of fragmented supply chains in African markets.
- Provides **transparent bidding** instead of opaque pricing.
- Gives **local suppliers** global-level digital exposure.
- Ensures **scalability** with microservices and cloud infrastructure.

  

✅ **Short Interview Pitch (if interviewer asks "Tell me about this project")**:  
"I worked on the DAI Project, which is a B2B supply chain and bidding platform targeted at African markets like Uganda and Tanzania. The system connects suppliers and buyers – suppliers can showcase products, buyers can place bids, and if quotations match, transactions are completed via an integrated payment gateway. We built it using Java microservices (Spring Boot), MongoDB, and AWS services. The platform has multiple environments – dev, stage, demo, prod, and a unique post-production environment which is a replica of production for safe testing. I was mainly involved in building the backend services such as management, notification, and payment, ensuring proper workflows between suppliers, buyers, and admins."

  

  

  

  

1. **Why we are using web socket:** 

- our project uses WebSocket because it's building a **real-time collaborative application** where multiple users need to work together on forms simultaneously. For example affiliation process, if one provider already added affiliation request to another provider, the other provider should not again request for affiliation. REST APIs are designed for request-response patterns and cannot provide the real-time, bidirectional communication that collaborative applications require. WebSocket enables instant updates, live collaboration, Real-time user status if he is online or not. So overall WS provide better user experience that would be impossible to achieve with traditional REST APIs.

**Why did you choose ConcurrentHashMap for caching? Why not use Redis or EHCache?**

It’s thread-safe, lock-free for reads, and performs better under concurrent access. For a high-throughput system like ours, where multiple users can access forms simultaneously, ConcurrentHashMap provides fine-grained locking (per bucket/segment), so multiple threads can safely read/write without corrupting data.

  

  

In-memory caching using ConcurrentHashMap was sufficient in our case. It was Simple and no external dependencies or **setup needed.** **Since our** Team was already familiar with Java collections we could build it quickly.

  

Redis/EHCache could be overkill for our simple use case.

  

**Can you explain how your O(1) lookup works?**

Earlier, to find a field inside nested sections/groups, we performed recursive traversal. Instead, I built a precomputed index (Map<fieldId, Section/Field metadata>) at load time. So whenever we get a referFrom request, we directly fetch metadata in O(1) instead of O(n).

  

  

  

1. How Indexing is actually helpful
2. Why and how Kafka?
3. Why cashing , how cashing. 

4. Java Memory model

5. CI/CD flow : Jenkins

6. Ingress file

7. Scaling database

  

  

  

**3. MongoDB Optimization**

- **"Can you walk me through the specific aggregation pipeline optimizations you made?"**
- **"How did you handle the different field types (multi-entry, table, normal) in your queries?"**
- **"What indexes did you create to support these optimizations?"**
- **"How did you ensure query performance consistency across different data volumes?"**

**7. Code Quality & Testing**

- **"How did you ensure your caching logic was thread-safe?"**
- **"What unit tests did you write for the caching functionality?"**
- **"How did you test the performance improvements?"**

💡 **Problem-Solving & Design Questions**

**8. Alternative Solutions**

-   
    
- **Did you consider using MongoDB's built-in caching mechanisms?**
- **"What other optimization strategies did you evaluate?”**

  

  

  

- **DB URLs:** 

  

  

Make documentation of your work  
  
Make documentation what analysing you are doing : what problem it is solving, solution its providing, what we will do, how we will do. What are the challenges will be there to implement this.