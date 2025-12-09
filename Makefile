# Production Deployment Scripts

# Build and start all services
up:
	docker-compose up -d --build

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-celery:
	docker-compose logs -f celery-worker celery-beat

# Restart services
restart:
	docker-compose restart

# Check status
status:
	docker-compose ps

# Clean up everything (WARNING: Removes volumes)
clean:
	docker-compose down -v
	docker system prune -f

# Production deployment
deploy:
	@echo "Building and deploying..."
	docker-compose -f docker-compose.yml up -d --build
	@echo "Deployment complete!"

# Database backup
backup:
	docker exec mailguard-mongodb mongodump --out=/data/backup/$(shell date +%Y%m%d_%H%M%S)

# Scale workers
scale-workers:
	docker-compose up -d --scale celery-worker=4