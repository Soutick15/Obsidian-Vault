
# DOCKER

## What is Server 

Server is nothing but one physical computer where our application is running.

 >[!danger] Before Docker – What Were the Problems?

 Earlier, one server could run only one application. 

Different apps needed different environments (Java 8 vs Java 11, MySQL vs Postgres). Lets say App-A needs Java 8 + MySql and App B needs Java 11 + MongoDB to run.

Running multiple apps on the same server caused conflicts.  

Dependency Hell

Our local computer is having one particular environment, like particular OS, different packages, modules etc are installed, 

So if the code works on your laptop it does not mean it will work on other computer as well. If the same environment (OS, versions) is not present on the other computer the code will not work because of different OS, packages, library versions etc.

To run the app in every machine, we needed the exact same environment where the code is developed and tested. So each time developers had to manual install all the Dependencies (same OS, same Java version etc)

What if we want to run Multiple application on a same system, it was not possible earlier? So this problem is solved by Virtual Machine or Virtualization (dividing one physical machine into many “virtual” machines).


## Virtual Machine 

Multiple applications can run on one server. Its own Operating System (OS) (Windows/Linux/Ubuntu etc.). Using a software called Hypervisor (like VMware, VirtualBox, Hyper-V) we can run different OS on top of the main computer it runs inside your existing OS.  Hypervisor splits hardware resources (CPU, RAM, Disk) and assigns them to multiple VMs.
- Each VM runs its own OS → so on one laptop you could have:

- VM1: Ubuntu
- VM2: Windows
- VM3: RedHat Linux

### Problems with VMs

- Each VM required a full OS, Every OS require the dedicated hardware resources to run. So high in RAM & CPU usage. 
- So they were slow, huge in size, and consumed a lot of CPU/RAM. 
- If you need 10 apps, you might spin 10 VMs, so it was expensive and slow.

  

>[!success] So to solve this problem Containers come into picture. 

- What Docker Solved
### Containers : 

It runs on top of VM. With Docker Multiple apps can run on one server using container. Each container has its own environment. We don’t need different operating systems, using one operation system we can run multiple applications sharing the same OS. So its Much faster and lighter than VMs.

No More Dependency Hell : All dependencies (OS libraries, packages, frameworks, language versions) are packed inside the Docker image. If it runs in your container, it will run on any machine (local, test, prod).

  

## DOCKER: 

- It’s a platform that assists in building images. Using Docker, we will create our images that will contain our environment.

### DOCKER FILE:

- Its an executable text file having list of instructions to create docker images. (Run this command, use this port etc.). The Dockerfile has the instructions (like FROM, COPY, RUN, CMD). Docker takes those instructions and builds an image.
- Example: 

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "start"]
```

```dockerfile
# Use Java 11 as base.
FROM openjdk:11

# Copy our jar file.
COPY target/app.jar app.jar

# Run the jar.
CMD ["java", "-jar", "app.jar"]
```

### DOCKER IMAGES:

- Blueprint of our application. It just a file which contains all the instructions like code, dependencies, libraries, configurations, even a tiny OS layer.
- We give this image(instructions) to other computer to run the program. 
- We build a Docker Image once and use it anywhere.

### DOCKER CONTAINER: 

- Containers are like a running instance that is created from docker images. like running a .jar with java -jar
- single unit (App+ All Development )
- It runs our application in isolation, means it has nothing to do with the outside environment like the OS, or the configuration. But without the OS any application can’t run, so docker container also contains OS and the other dependencies to run the application.
- docker-compose.yml = orchestrator to run multiple containers with one command (docker-compose up).

Runtime : Allow us to start and stop containers. 2 types- 

1. run c: to work with OS to start and 

2. Container d : Managing run c also help managing containers,

  

Docker Engine: docker cli(client)  -> Rest API-> server, daemon

Docker Layers: Images are built 

### IMAGES :

```bash
# List all images that is present on our local system
docker images 
```

```bash
# delete an image
docker rmi <image_name_or_id>
```

  ```bash
# Remove unused/dangling images
docker image prune
  ```

```zsh
# Build image from Dockerfile (version/tag is optional)
docker build -t <image_name>:<version> 
```

```bash
# Build image without using cache

docker build --no-cache -t <image_name>:<version>
```
    
---

### CONTAINER :

```bash
# List all containers (running + stopped)
docker ps -a
```

```bash
# List only running containers
docker ps
```

```bash
# Run a new container (downloads image if not present locally)
docker run <image_name>
```


```bash
# Run container in background
docker run -d <image_name>
```
  

```bash
# Run container with a custom name
docker run --name <container_name> <image_name>
```

```bash
# Port binding (host:container)
docker run -p <host_port>:<container_port> <image_name>
```

```bash
# Set environment variable(s) inside container
docker run -e <VAR_NAME>=<value> <image_name>
```

```bash
# Start a stopped container
docker start <container_id_or_name>
```

```bash
# Stop a running container
docker stop <container_id_or_name>
```

```bash
# Inspect a container (get full details in JSON format)
docker inspect <container_id_or_name>
```


```bash
# Delete/remove a container
docker rm <container_id_or_name>
```

---
### TROUBLESHOOT :
  
```bash
# Get logs of a container
docker logs <container_id_or_name>
```

  ```bash
# Open shell inside a running container
docker exec -it <container_id_or_name> /bin/bash
  ```

  ```bash
# Alternate shell (for alpine or lighter images)
docker exec -it <container_id_or_name> sh
  ```

  
---
### DOCKER HUB :

```bash
# Pull an image from Docker Hub
docker pull <image_name>
```

  ```bash
# Push an image to Docker Hub
docker push <username>/<image_name>
  ```

```bash
# Login to Docker Hub
docker login -u <username>

# Or simply
docker login
```

  ```bash
# Logout from Docker Hub
docker logout
  ```

  ```bash
# Search for an image on Docker Hub
docker search <image_name>
  ```

  ---  
### VOLUMES :

  ```bash
# List all Docker volumes
docker volume ls
  ```

  ```bash
# Create a new named volume
docker volume create <volume_name>
  ```

  ```bash
# Delete a named volume
docker volume rm <volume_name>
  ```

  ```bash
# Mount a named volume inside container
docker run --volume <volume_name>:<mount_path> <image_name>
  ```

  ```bash
# Mount a named volume using --mount (more control)
docker run --mount type=volume,src=<volume_name>,dst=<mount_path> <image_name>
  ```
  
```bash
# Mount an anonymous volume (auto-generated name)
docker run --volume <mount_path> <image_name>
```

```bash
# Bind mount from host to container
docker run --volume <host_path>:<container_path> <image_name>
```

 ```bash
# Bind mount using --mount
docker run --mount type=bind,src=<host_path>,dst=<container_path> <image_name>

 ```  

```bash
# Remove unused volumes (usually anonymous)
docker volume prune
```

---
### DOCKER NETWORKING (ADVANCED) : 

  

  
---

## Orchestration:

- Now using docker we create containers. Now think of we have 100 containers running across 5 servers. 
- Some containers crash at midnight?
- Traffic suddenly spikes → you need more replicas?
- You want to update your app with zero downtime?
- Now manually managing these containers it is a complicated task. So we needed the way to automate the  process of managing the containers. 
- So here Orchestration comes into the picture. It allow us to manage containerized applications automatically. 

### Kubernetes

Kubernetes (aka K8s) is an open-source container orchestration platform. It helps you deploy, scale, and manage containerized applications automatically.

#### Advantages of Kubernetes :

- Eliminates “it works on my machine” problem → portable across cloud & on-prem.
- Automates scaling (up/down based on load).
- Ensures self-healing (restarts crashed Pods).
- Rolling updates & zero-downtime deployments.
- Standard in microservices + cloud-native apps.

  
---

##### Pods 
A smallest deployable unit that goes inside Kubernetes. Its a running instance of our app, like it is a wrapper around one or more containers running together.(like Docker containers), with shared Network (they talk to each other via localhost), Storage (if mounted), Lifecycle (they start/stop together).

Kubernetes manages pods by creating more instance of it to balance the load.

##### Node / Worker Node
A Physical or virtual computer that runs multiple Pods. Since its a computer it Provides CPU, memory, and networking for Pods. Managed by control plane / kubelet. we have kubelet, Kuber-proxy installed inside Node.

##### kubelet
This is an Agent running on each node. It Ensures Pods run as expected by communicating with the API server.

##### Kube-proxy
Handles networking and load balancing inside the cluster. Routes traffic to Pods via Services.

---
#### Control Plane Components : 

##### API Server (kube-apiserver)
This is the entry point where developers hit With deployment, config, instruction etc. developers use API server to interact with Control plane. 

##### Controller (kube-scheduler) 
API server communicates with Controller : It execute

##### Etcd 
A distributed key-value store that stores the cluster’s state and configuration. Provides consistency and recovery in case of failure

##### Schedular (kube-scheduler)
Decides which node a Pod should run on based on resource availability, constraints, and policies.

##### Controller Manager (kube-controller-manager)
Monitors the cluster state and makes corrections to reach desired state. Examples: Deployment controller, Node controller, ReplicaSet controller.

  

##### replica
A replica is basically a copy of a Pod that Kubernetes keeps running to ensure high availability.


---

### How do you handle scaling in Kubernetes : 

There are two main types of scaling: 

1. Horizontal Scaling (scale out/in) : add or remove Pods.
2. Vertical Scaling (scale up/down) – increase or decrease resources (CPU/memory) of a Pod.

I usually use Horizontal Pod Autoscaler (HPA), which can scale Pods automatically based on CPU, memory, or custom metrics. For example, I can configure HPA on a Deployment to keep CPU usage around 50%, and it will automatically increase or decrease the number of Pods. I can also manually scale Pods using kubectl scale deployment `<name> --replicas=<number>`

Vertical scaling adjusts the CPU or memory of existing Pods using Vertical Pod Autoscaler (VPA).

At the cluster level, if all nodes are full, I can use a Cluster Autoscaler to add more nodes, and remove them when utilization is low.

### Worker node components :


