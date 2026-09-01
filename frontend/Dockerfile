FROM node:18-alpine

ARG API_URL=http://127.0.0.1:8000
ENV API_URL=$API_URL

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
