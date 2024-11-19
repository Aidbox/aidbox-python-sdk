seeds:
	docker compose up -d build-seeds
	docker compose up -d --force-recreate --no-deps aidbox

up:
	docker compose pull --quiet
	docker compose build
	docker compose up -d

stop:
	docker compose stop

down:
	docker compose down


