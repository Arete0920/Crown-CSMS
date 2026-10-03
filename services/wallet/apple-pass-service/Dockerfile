FROM node:24-alpine
LABEL maintainer="Crown Engineering"

RUN apk add --no-cache openssl

WORKDIR /app

# Install dependencies first (cache layer)
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

# App source
COPY server.js ./

EXPOSE 7071
CMD ["node", "server.js"]
