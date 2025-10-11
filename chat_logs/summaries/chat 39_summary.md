## 1. High-Level Objective ##

To debug and successfully deploy a Python application with an Nginx proxy using Docker Compose on an AWS EC2 instance.

## 2. Key Architectural Decisions & Features Implemented ##

* Increased EC2 instance storage from 30GB to 70GB to resolve "no space left on device" errors during Docker build.
* Corrected the `docker-compose.yml` file to include the correct `build.context: ./python_agent_runner` directive, allowing the Docker build to find the `requirements.txt` file within the subdirectory.
* Implemented a complete `docker-compose.yml` file defining both the Python application service (`miso_app`) and the Nginx proxy service with correct port mappings, dependencies, and build contexts.


## 3. Final Code State ##

```yaml
version: '3.8'

services:
  miso_app:
    build:
      context: ./python_agent_runner
      dockerfile: Dockerfile
    expose:
      - "5000"

  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - miso_app

```

## 4. Unresolved Issues & Next Steps ##

* Existing stopped containers caused a naming conflict. Next steps include running `sudo /usr/local/bin/docker-compose down` to remove old containers and then `sudo /usr/local/bin/docker-compose up --build -d` to start the application fresh.
