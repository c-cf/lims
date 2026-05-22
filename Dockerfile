FROM nginx:1.27-alpine

COPY nginx/templates /etc/nginx/templates
COPY . /usr/share/nginx/html

EXPOSE 80
