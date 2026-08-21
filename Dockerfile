# 1. Use an official, lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all your Python scripts into the container
COPY . .

# 5. Expose the port Streamlit uses
EXPOSE 8501

# 6. Set the command to run your Streamlit dashboard
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]