cd ai_engine
# Node.js
npm run dev
# Run migrations
ts-node src/index.ts
# Send test request
curl -X POST http://localhost:4000/ai/trace \
  -H "Content-Type: application/json" \
  -d '{"studentId":"...","conceptId":"...","correct":true}'
