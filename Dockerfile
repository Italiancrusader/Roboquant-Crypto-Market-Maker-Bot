FROM python:3.10-slim

# Create and set working directory
WORKDIR /app

# Copy local files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the bot
CMD ["python", "bot.py"]
