#!/bin/bash

up() {
    docker-compose -f ../docker-compose.yml up --build
}

down() {
    docker-compose -f ../docker-compose.yml down
}

test() {
    docker-compose -f ../docker-compose.yml exec api pytest
}

lint() {
    (cd .. && python3 -m pre_commit run --all-files)
}

echo "uruchomiono... "
echo "Dostępne komendy: up, down, test, lint"
