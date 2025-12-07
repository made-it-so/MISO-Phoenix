













## Local Development Troubleshooting (Updated)

### Database Connection
If running locally (outside Docker network), override the default host:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/miso_db"
```

### Port Conflicts (Address already in use)
If Docker containers fail to start, ensure Ubuntu system services aren't hogging the ports:
```bash
# Stop system Redis and Postgres
sudo service redis-server stop
sudo service postgresql stop
```

## Troubleshooting (Updated)

### Port Conflicts
If Docker fails to bind ports (e.g., 5432 or 6379), stop the system services:
```bash
sudo service redis-server stop
sudo service postgresql stop
```

## Docker Troubleshooting (Updated)

### Stale Dependencies
If you add a package to `requirements.txt` but the container complains it's missing, force a clean build:
```bash
docker compose build --no-cache
```

### Port Conflicts
If containers fail to start with "Address already in use", stop the system services:
```bash
sudo service redis-server stop
sudo service postgresql stop
```
