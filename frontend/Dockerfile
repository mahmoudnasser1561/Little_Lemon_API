# Dev-mode image: runs Vite's own dev server with hot reload, not a production build.
# docker-compose bind-mounts the whole monorepo over /app, so further frontend work
# happens by editing files on the host - this image's job is just to have the workspace
# installed and to run `vite --host` so the container is reachable from outside itself.
# A production (static build + nginx) image is a separate, later concern - out of scope
# for this dev-loop container.
FROM node:22-alpine
WORKDIR /app

# Installed in a layer keyed on the package manifests only, so `docker compose build`
# doesn't reinstall on every source change - only when a package.json/lockfile changes.
COPY package.json package-lock.json ./
COPY apps/storefront/package.json apps/storefront/package.json
COPY apps/ops-console/package.json apps/ops-console/package.json
COPY packages/api-client/package.json packages/api-client/package.json
COPY packages/ui/package.json packages/ui/package.json
RUN npm install

COPY . .

# No WORKDIR/CMD here - docker-compose sets working_dir and command per service, so
# one image serves both apps/storefront and apps/ops-console.
