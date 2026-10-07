FROM node:24-alpine
LABEL maintainer="Crown Engineering"

RUN apk add --no-cache openssl

WORKDIR /app

# Install dependencies first (cache layer)
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

# App source
COPY --chown=node:node server.js ./

EXPOSE 7071

# Run the service without root privileges.
USER node
CMD ["node", "server.js"]
