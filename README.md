













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
