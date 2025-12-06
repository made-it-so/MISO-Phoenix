```markdown
## 1. High-Level Objective

To replace the placeholder `alpha_frontend` service with a basic React application that establishes a persistent WebSocket connection to the `alpha_backend` and displays the connection status.

## 2. Key Architectural Decisions & Features Implemented

* **Reverted from ECS/Fargate to EC2:** Abandoned the non-functional ECS architecture and returned to a working EC2-based deployment.
* **Corrected Backend WebSocket Handling:** Fixed the `alpha_backend` code and deployment to correctly handle WebSocket connections.
* **Simplified Frontend for Debugging:** Created a minimal HTML/JavaScript frontend to isolate connection issues.
* **Fixed CI/CD Pipeline:** Removed obsolete ECS deployment jobs from the `.github/workflows/deploy.yml` file and ensured the pipeline only builds and pushes Docker images.

## 3. Final Code State

```yaml
name: MISO Factory - CI/CD Pipeline
on:
  push:
    branches:
      - main
env:
  ECR_REGISTRY: ${{ secrets.ECR_REGISTRY }}
  AWS_REGION: us-east-1
jobs:
  build-and-push:
    name: Build and Push Images
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      - name: Log in to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build and Push all images
        run: |
          set -e
          docker build -t $ECR_REGISTRY/alpha_backend:latest -f ./alpha_backend/Dockerfile .
          docker build -t $ECR_REGISTRY/alpha_frontend:latest -f ./alpha_frontend/Dockerfile .
          docker build -t $ECR_REGISTRY/embedding-service:latest -f ./embedding-service/Dockerfile .
          docker build -t $ECR_REGISTRY/miso_agent:latest -f ./miso_agent/Dockerfile .
          docker build -t $ECR_REGISTRY/resource-broker:latest -f ./resource-broker/Dockerfile .
          docker build -t $ECR_REGISTRY/kernel-service:latest -f ./kernel-service/Dockerfile .
          docker build -t $ECR_REGISTRY/council-service:latest -f ./council-service/Dockerfile .
          docker push --all-tags $ECR_REGISTRY/alpha_backend
          docker push --all-tags $ECR_REGISTRY/alpha_frontend
          docker push --all-tags $ECR_REGISTRY/embedding-service
          docker push --all-tags $ECR_REGISTRY/miso_agent
          docker push --all-tags $ECR_REGISTRY/resource-broker
          docker push --all-tags $ECR_REGISTRY/kernel-service
          docker push --all-tags $ECR_REGISTRY/council-service
```

## 4. Unresolved Issues & Next Steps

* **Deploy the application:** Manually run the `./definitive_genesis.sh` script on the EC2 server to deploy the updated application.  No unresolved bugs are explicitly mentioned, but successful connection of the simplified frontend was not confirmed in the log.
```
