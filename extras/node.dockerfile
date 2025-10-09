FROM node:22-bookworm
WORKDIR /app


# Environment for Vite (if you’ll add later)
ENV HOST=0.0.0.0
EXPOSE 5173

# Default command (will fail if npm scripts don’t exist yet)
CMD ["npm", "run", "dev", "--", "--host"]
