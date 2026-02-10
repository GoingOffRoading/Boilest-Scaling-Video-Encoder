# Deployment Examples

This directory contains deployment configurations for Boilest in different environments.

## Docker Compose Deployment

For single-host Docker deployments, use the `docker-compose.yml` file.

### Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your media path:
   ```
   MEDIA_PATH=/path/to/your/media
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Scale workers as needed:
   ```bash
   docker-compose up -d --scale boilest-worker=3
   ```

5. Access the manager UI at: http://localhost:31500

### Notes
- Manager service runs on port 31500
- Workers automatically connect to the manager
- All media paths are mounted as specified in the `.env` file

## Kubernetes Deployment

For multi-node Kubernetes clusters, use the `Boil.yml` file.

### Prerequisites
- A running Kubernetes cluster
- Persistent Volume Claim named `media-pvc` for media storage
- Nodes labeled with `boilest: manager` and `boilest: worker`

### Setup

1. Apply the configuration:
   ```bash
   kubectl apply -f Boil.yml
   ```

2. Access the manager UI via NodePort 31500

### Notes
- Manager uses nodeSelector `boilest: manager`
- Workers use nodeSelector `boilest: worker`
- Workers run as a DaemonSet (one per worker node)
- Update `MANAGER_BASE_URL` in worker env if needed
