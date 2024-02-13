# Postgres Chatbot

The Postgres Chatbot is an advanced AI-powered interface designed to interact with PostgreSQL databases through natural language prompts. By leveraging large language models (LLMs), this chatbot can generate SQL queries based on user inputs, making database interactions intuitive and efficient.

## Features

- **Natural Language Processing**: Interact with your PostgreSQL database using natural language prompts.
- **Dynamic SQL Query Generation**: Automatically generates SQL queries from user prompts.
- **Environment Variable Configuration**: Securely configures database and API keys using environment variables.
- **Flexible Response Formatting**: Customizable response formatting to suit different use cases.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10 or newer
- PostgreSQL server (accessible via the provided `DATABASE_URL`)
- An OpenAI API key for accessing large language models

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/AlisherAmirbek/postgres_ai_chatbot.git
   cd postgres_chatbot

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt

3. **Set up environment variables**

   Access .env file in the root directory of the project and change it with your PostgreSQL connection URL and OpenAI API key:
    ```bash
    DATABASE_URL=postgres://your_user:your_password@your_host:your_port/your_db
    OPENAI_API_KEY=your_openai_api_key

## Usage

Run the chatbot with a prompt as follows:

```bash
python postgres_chatbot.py --prompt "Your natural language prompt here"
```
For example:


```bash
python postgres_chatbot.py --prompt "List all employees in the Sales department"
```

The chatbot will process the prompt, generate an SQL query, execute it against the configured PostgreSQL database, and return the results.

## Customization

* Table Definitions and Response Formats: Customize the SQL generation by modifying the POSTGRES_TABLE_DEFINITIONS_CAP_REF and RESPONSE_FORMAT_CAP_REF in the script to match your database schema and desired output format.

* Advanced Configuration: Dive into the modules directory to adjust the database connection and LLM interaction settings as per your requirements.
