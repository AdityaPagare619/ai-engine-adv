FROM node:18-alpine

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

RUN apk add --no-cache bash curl jq

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f https://localhost:8080/health || exit 1

CMD ["node", "src/index.js"]
