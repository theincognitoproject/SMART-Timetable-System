FROM node:18-alpine

WORKDIR /app

# Copy only package files first for better caching
COPY package*.json ./
RUN npm install

# Copy rest of the source
COPY . .

# Set environment
ENV NODE_ENV=development

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
