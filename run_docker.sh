
docker build -t workout-review-app .

docker run -p 8501:8501 \
  -e url="${url}" \
  -e key="${key}" \
  workout-review-app
