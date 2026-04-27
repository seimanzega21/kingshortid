#!/bin/bash
docker exec $(docker ps -qf name=supabase-db) psql -U supabase_admin -d postgres -c "DELETE FROM dramas WHERE total_episodes <= 2;"
