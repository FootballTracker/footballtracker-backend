#!/bin/bash


echo -e "\n\nTesting auth/signin"
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword"
}'
