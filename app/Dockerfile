# Use the official Python image as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
RUN pip install --upgrade pip
# Install any needed packages specified in requirements.txt
RUN cat requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN export OPENAI_API_KEY=${OPENAI_API_KEY}

RUN export LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}

RUN export OPENCAGE_API_KEY=${OPENCAGE_API_KEY}

RUN export TAVILY_API_KEY=${TAVILY_API_KEY}

RUN export DB_URI=${DB_URI}

RUN export DATABASE_NAME=${DATABASE_NAME}

RUN export MONGODB_URI=${MONGODB_URI}

RUN export LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}

RUN export LOG_LEVEL=${LOG_LEVEL}

# Make port 80 available to the world outside this container
EXPOSE 80



# Run the FastAPI application
CMD ["uvicorn", "main:app","--host", "0.0.0.0", "--port", "80"]