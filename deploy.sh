#!/bin/sh
set -eu
image="$1"
name=midterm-api
candidate=midterm-api-candidate
previous=midterm-api-previous
docker rm -f "$candidate" >/dev/null 2>&1 || true
docker run -d --name "$candidate" -p 127.0.0.1:18000:8000 "$image"
trap 'docker rm -f "$candidate" >/dev/null 2>&1 || true' EXIT
ready=0
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18000/metrics > /tmp/midterm-candidate-metrics.json; then ready=1; break; fi
  sleep 2
done
test "$ready" = 1
docker rm -f "$previous" >/dev/null 2>&1 || true
if docker inspect "$name" >/dev/null 2>&1; then
  docker stop "$name" >/dev/null
  docker rename "$name" "$previous"
fi
if docker run -d --name "$name" --restart unless-stopped -p 8000:8000 "$image"; then
  for attempt in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8000/metrics; then
      docker rm -f "$previous" >/dev/null 2>&1 || true
      exit 0
    fi
    sleep 2
  done
fi
docker logs "$name" 2>&1 || true
docker rm -f "$name" >/dev/null 2>&1 || true
if docker inspect "$previous" >/dev/null 2>&1; then
  docker rename "$previous" "$name"
  docker start "$name" >/dev/null
fi
exit 1
