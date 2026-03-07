FROM node:20-alpine
LABEL maintainer="Crown Engineering"

WORKDIR /app

# Install dependencies first (cache layer)
COPY package.json ./
RUN npm install --omit=dev

# App source
COPY server.js ./

EXPOSE 7071
CMD ["node", "server.js"]
