import os
from modules.db import PostgresManager
from modules import llm
import dotenv
import argparse

dotenv.load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", help="Prompt for the chatbot")
args = parser.parse_args()

assert os.environ.get("DATABASE_URL"), "POSTGRES_CONNECTION_URL not found in .env file"
assert os.environ.get(
    "OPENAI_API_KEY"
), "POSTGRES_CONNECTION_URL not found in .env file"

DB_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"

SQL_DELIMITER = "---------"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return
    prompt = f"Fulfill this database query: {args.prompt}. "
    prompt += "\n\nImportant: Always enclose table and column names in double quotes if they contain uppercase letters or are created with case sensitivity. Do not wrap the SQL query in triple backticks (```)."
    prompt += "\n\nFor instance, correctly format a query like: SELECT \"EmployeeId\", \"Name\" FROM \"Employees\" WHERE \"Department\" = 'Sales';"
    prompt += "\nAn incorrect format would be: SELECT EmployeeId, Name FROM Employees WHERE Department = 'Sales'; or wrapping the query in ```."


    with PostgresManager() as db:
        db.connect_with_url(DB_URL)

        table_definitions = db.get_table_definitions_for_prompt()

        prompt = llm.add_cap_ref(
            prompt,
            f"\n\nUse these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        prompt = llm.add_cap_ref(
            prompt,
            f"\n\nRespond in this format {RESPONSE_FORMAT_CAP_REF}. Replace the text between <> with it's request. I need to be able to easily parse the sql query from your response.",
            RESPONSE_FORMAT_CAP_REF,
            f"""<explanation of the sql query>
{SQL_DELIMITER}
<sql query exclusively as raw text>""",
        )

        print("\n\n-------- PROMPT --------")
        print(prompt)

        prompt_response = llm.prompt(prompt)

        print("\n\n-------- PROMPT RESPONSE --------")
        print(prompt_response)

        sql_query = prompt_response.split(SQL_DELIMITER)[1].strip()
        print(f"\n\n-------- PARSED SQL QUERY --------")
        print(sql_query)

        result = db.run_sql(sql_query)

        print("\n\n======== POSTGRES DATA ANALYTICS AI AGENT RESPONSE ========")

        print(result)


if __name__ == "__main__":
    main()
