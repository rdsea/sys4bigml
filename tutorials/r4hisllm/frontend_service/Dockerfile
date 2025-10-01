# Use lightweight Nginx image to serve static files
FROM nginx:alpine

# Remove default nginx static content
RUN rm -rf /usr/share/nginx/html/*

# Copy frontend files
COPY ./ /usr/share/nginx/html

# Set proper permissions
RUN chmod -R 755 /usr/share/nginx/html

# Expose port 80
EXPOSE 80 

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

